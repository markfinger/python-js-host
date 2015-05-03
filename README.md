# python-js-host

[![Build Status](https://travis-ci.org/markfinger/python-js-host.svg?branch=master)](https://travis-ci.org/markfinger/python-js-host)

Python bindings to a performant JavaScript environment.

There are a variety of libraries which provide access to JS engines, PyExecJS et al, but they only provide 
basic functionality, suffer performance problems, and introduce setup overhead. Rather than provide low-level 
hooks to evaluate JavaScript, this library hooks in to an
[opinionated JavaScript layer](https://github.com/markfinger/js-host) which runs persistent and performant 
environments built for easy configuration.

In [development](#usage-in-development), a [manager process](#jshostmanager) is provided to reduce integration overheads by automatically spawning hosts in the background.

In [production](#usage-in-production), the same codebase is used to connect to environments which you can easily
run under your own supervisor process.


Installation
------------

```bash
pip install js-host
```


Dependencies
------------

[node](nodejs.org) or [io.js](https://iojs.org/)

[js-host](https://github.com/markfinger/js-host)


Quick start
-----------

Create a `package.json` file by running the following

```bash
npm init
```

Install the `js-host` JavaScript library with

```bash
npm install js-host --save
```

Create a file named `host.config.js` and insert the following

```javascript
module.exports = {
  functions: {
    hello_world: function(data, cb) {
      var name = data.name || 'World';
      cb(null, 'Hello, ' + name + '!');
    }
  }
};
```

Open a python shell and run the following

```python
import js_host.conf

js_host.conf.settings.configure(USE_MANAGER=True)
```

If everything went ok, you should see some output as the manager process spins up and then spawns a host 
which runs an environment using your `host.config.js` file.

In the same python shell, run the following

```
from js_host.function import Function

hello_world = Function('hello_world')

hello_world.call()

hello_world.call(name='Foo')
```

:hatched_chick:


API
---


### Function

`Function` objects enable you to pass data from your python process to a JavaScript environment. Functions 
must be created with a string which matches a name specified in your config file.

If your `host.config.js` file resembled the following

```javascript
module.exports = {
  functions: {
    greeter: function(data, cb) {
      cb(null, 'Hello');
    },
    double: function(data, cb) {
      if (!data.number) {
        return cb(new Error('No number was provided');
      }
      cb(null, data.number * 2);
    }
  }
};
```

You can call those functions from Python with the following

```
from js_host.function import Function

greeter = Function('greeter')

greeter.call()  # returns 'Hello'

double = Function('double')

double.call(number=20)  # returns '40'

double.call()  # raises a error 'No number was provided'
```

Keyword arguments provided to `call` are passed to the JS host as JSON, and they are provided
to your function as its first argument. The second argument to your function is a callback 
which your function calls to indicate that it has completed. 

To indicate an error condition from your function, pass an `Error` object as the callback's 
first argument. To indicate a success condition, invoke the callback with `null` as the first 
argument and your value as the second argument.

Your functions can complete their task either synchronously or asynchronously. Once the callback 
has been passed a value, the host assumes that the function has completed and sends a response 
back to the Python process.

For more information on the API and behaviour of functions, refer to the 
[js-host documentation on functions](https://github.com/markfinger/js-host#functions).


### JSHost

`JSHost` objects read in your config files and act as bridges to JS environments using those same
config files.

If you want to introspect a running host, there are some utils provided to assist you

```
from js_host.host import host

# An absolute path to the node binary used to run hosts
self.path_to_node

# An absolute path to the `js-host` library used
self.get_path_to_bin()

# Returns an absolute path to the config file used by the host
host.get_path_to_config_file()

# Returns a URL which points to the location of the host on your network
host.get_url()

# Returns a dict containing information that the host reported during startup
host.get_status()

# Connects to a running host and returns information about the environment
host.request_status()

# Returns True/False if a host process is running at the expected url
host.is_running()

# Connect to an environment and validate that it matches your config
host.connect()
```

If you are using the manager to control your hosts, the following utils are also available on 
`JSHost` objects

```python
from js_host.host import host

# the JSHostManager instance that the host uses
host.manager

# An absolute path to a file that the managed host writes its logs to
host.logfile

# Connect to the manager and ask it to spawn a host using the host's config file
host.start()

# Connect to the manager and ask it to stop the host
host.stop()

# Connect to the manager and ask it to respawn the host
host.restart()
```

### JSHostManager

`JSHostManager` objects provide an interface to a detached process which runs on your local network 
and spawns [js-host](https://github.com/markfinger/js-host) instances on demand.

Note: do **not** use the manager in production, it only aims to solve issues relating
to the typical development environment. Please refer to the 
[usage in production](#usage-in-production) section before setting up a production
environment.

The primary benefit of using a manager is that it abstracts away the bother of spawning a host 
manually. During development, your primary goal is to build things - the complexities of running 
processes should be left to production environments.

Under the hood, managers are spun up in a child process which blocks the python process until 
the manager is running. The child process spawns the manager in another process which is completely 
detached from your python process. Using a detached process allows the manager and its hosts to 
persist even when the python process has restarted or exited.

Once a manager is running, it starts listening for incoming requests which indicate that an 
external process wants it to spawns a new js-host which uses a particular config file. Once the 
new instance has been spawned, the python process asks the manager to register a new connection 
to the host. 

When your python process exits, it quickly sends a disconnection signal to the manager, notifying
the manager that any hosts spawned are no longer required. Once a spawned host's connections have 
all closed, the manager waits 5 seconds for any new connections to be opened, before it stops the 
host's process.

To clean up after itself, a manager will stop its own process once every host has been stopped.

Be aware that managers have some quirks:

- Managed hosts can persist after their config file has changed.
  
  To force a restart, call the `restart` method of a `JSHost` instance. For example
  ```python
  from js_host.host import host
  host.restart()
  ```
- Managers and managed hosts run in processes detached from your shell, which can make it difficult 
  to inspect their output streams.

  To provide some measure of introspection, managed hosts write their output to logfiles which are 
  stored in your OS's temporary directory. The `logfile` attribute on a managed `JSHost` instance 
  provides an absolute path to the file. For example
  ```python
  from js_host.host import host
  print(host.logfile)
  ```
- If a function triggers an unhandled exception and crashes the host, the host will not be respawned
  until the python process restarts. 

  This behaviour is by design - respawning crashed hosts automatically simply hides the underlying 
  issue. If a crash is detected, exceptions will be raised indicating that you should inspect the
  logfile.

Be aware that managers have some identified issues:
- Managers and managed hosts are only compatible with OSX and *nix systems. Tracked in
  [js-host#7](markfinger/js-host#7)

If you experience unexpected behaviour or you simply want to avoid managers, you are recommended to 
set the `USE_MANGER` setting to `False`, and start hosts [manually](#usage-in-production).


Settings
--------

### SOURCE_ROOT

An absolute path to the directory which contains your node_modules directory.

This setting must be defined to start either a host or manager.

Default: `None`


### CONFIG_FILE

A path to the default config file used for hosts and managers.

If the path is relative, it is appended to `SOURCE_ROOT`.

Default: `'host.config.js'`


### USE_MANAGER

Indicates that a manager should be used to spawn host instances.

DO *NOT* USE THE MANAGER IN PRODUCTION.

Default: `False`


### PATH_TO_NODE

A path to a node or io.js binary

Default: `'node'`


### BIN_PATH

A path to the binary used to control hosts and managers.

If the path is relative, it is appended to the SOURCE_ROOT setting

Default: `os.path.join('node_modules', '.bin', 'js-host')`


### FUNCTION_TIMEOUT

Indicates how many seconds `Function` objects will wait for a response before
raising exceptions.

Default: `10.0`


### CONNECT_ONCE_CONFIGURED

Indicates that once `js_host` has been configured, it should attempt to connect to a
host.

This setting enables any config or connection errors to be raised during startup,
rather than during runtime. It also enables connections to managed hosts to be
preserved between restarts of your python process.

If you want to run multiple hosts and/or control the connection process, set this 
to `False`. Be aware that if you set it to `False`, managed hosts may not preserve 
connections when your python process restarts.

Default: `True`


### URL_OVERRIDE

Overrides the root url which requests are sent to.

By default, the root url is inferred from the config that the host generates from your file. 

If you want to route requests, set it to a string such as `'http://127.0.0.1:9009'`.

Default: `None`


### VERBOSITY

Indicates how much information the host should print the terminal. By default this
will print to the terminal whenever processes are started or connected to.

If you want to suppress all output, set it to `js_host.verbosity.SILENT`.

Default: `js_host.verbosity.PROCESS_START`


Django integration
------------------

Due to some quirks in how Django's configuration layer works, there are a few helpers
provided to integrate this library into a django project.

Rather than defining settings by using `js_host.conf.settings.configure(...)`, you
should place them into a dictionary named `JS_HOST` in your django settings files and add
`js_host` to your `INSTALLED_APPS` setting. For example

```
INSTALLED_APPS = (
    # ...
    'js_host',
)

JS_HOST = {
    'SOURCE_ROOT': '/path/to/your/project',
    'USE_MANAGER': DEBUG,
}
```

Once django has initialized, it will import `js_host` and trigger the app to start introspecting
the environment, configuring itself, and connecting to a js-host instance.


Usage in development
--------------------

In development, you are generally recommended to use managers as they abstract away the overhead 
of starting and stopping processes. To use a manager to spawn hosts, set `USE_MANAGER` to `True`
when configuring this library.

If you are writing code to be run on a host, it will typically be useful to have more immediate
feedback and control of a process. To start and control hosts yourself, refer to 
[js-host's CLI usage](https://github.com/markfinger/js-host#cli-usage).

If you want access to a REPL which enables you to inspect a JS environment, you can run a host 
with an [interactive debugger](https://github.com/markfinger/js-host#debugging-hosts)


Usage in production
-------------------

The major difference between development and production is that you are strongly recommended
to **not** use the manager in a production environment. Ensure that the `USE_MANAGER` setting is
set to `False` before you start your python processes.

In a production environment, you should run your hosts under a supervisor system, such as
[supervisor](http://supervisord.org/) or [PM2](https://github.com/Unitech/pm2). You can refer 
to [js-host's CLI usage](https://github.com/markfinger/js-host#cli-usage) for the necessary 
incantation to spin up a process under a supervisor. It will generally boil down to something 
like

```bash
node_modules/.bin/js-host host.config.js
```

### Logging

By default, js-host instances will only write their logs to stdout and stderr. Refer to js-host's 
documentation on [logging](https://github.com/markfinger/js-host#logging) if you want to configure
the logger yourself.

### Caching

js-host does not have its own caching layer, but an upstream caching layer can be implemented 
easily. All communication between the python processes and the js hosts is performed via HTTP. 
By placing a reverse proxy such as [varnish](https://www.varnish-cache.org/) between your python 
processes and the host itself, you can massively boost your response times, and reduce the load 
on the host.

By default, the urls to connect to a host are inferred from the config. To ensure that all requests
are sent to another address, define the `URL_OVERRIDE` setting as a complete url to your proxy. For 
example

```python
js_host.conf.settings.configure(
    # ...
    URL_OVERRIDE='http://127.0.0.1:1234',
)
```

The python layer will now send all requests to `http://127.0.0.1:1234`.


#### Caching requests

Requests are sent to hosts according to js-host's 
[endpoint definition](#https://github.com/markfinger/js-host#endpoints).

When the python layer sends requests to functions, it appends a `hash` paramater to the url, 
which is a `sha1` hash of the serialized data sent to the function. For example, a request to a 
function named `hello_world` with the data `{'foo': 'bar'}` will be sent as:

```
POST: /function/hello_world?hash=bc4919c6adf7168088eaea06e27a5b23f0f9f9da
```

This paramater enables you to cache a specific function's output by the data that was sent in.

Running the tests
-----------------

```bash
mkvirtualenv js-host
pip install -r requirements.txt
./runtests.sh
```
