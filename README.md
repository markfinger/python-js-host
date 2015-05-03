# python-js-host

[![Build Status](https://travis-ci.org/markfinger/python-js-host.svg?branch=master)](https://travis-ci.org/markfinger/python-js-host)

Python bindings to [js-host](https://github.com/markfinger/js-host), an opinionated JavaScript 
layer which runs persistent environments built for performance and easy configuration.

There are a variety of libraries which provide access to JS engines, PyExecJS et al, but they only 
provide basic functionality, suffer performance problems, and introduce setup overhead. This library 
enables you to hook in to persistent environments which have the full power, high performance, and vast
ecosystem offered by modern JS engines.

In [development](#usage-in-development), a [manager process](#jshostmanager) is provided to simplify
your workflow by automatically spawning environments in the background.

In [production](#usage-in-production), the same codebase is used to connect to environments which you 
can easily run under your own supervisor process.


Documentation
-------------

- [Installation](#installation)
- [Quick start](#quick-start)
- [Settings](#settings)
- [Usage in Django projects](#usage-in-django-projects)
- [Usage in development](#usage-in-development)
- [Usage in production](#usage-in-production)
  - [Logging](#logging)
  - [Caching](#caching)
    - [Caching requests](#caching-requests)
- [API](#api)
  - [Function](#function)
  - [JSHost](#jshost)
  - [JSHostManager](#jshostmanager)
    - [Under the hood](#under-the-hood)
    - [Quirks](#quirks)
    - [Issues](#issues)
- [Running the tests](#running-the-tests)


Installation
------------

```bash
pip install js-host
```

js-host requires access to a `node` binary provided by [Node.js](https://nodejs.org) or [io.js](https://iojs.org/).

On OSX you can install node with `brew install node`.

On Linux you can install node with `apt-get install nodejs` or a comparable command specific
to your distribution's package manager.


Quick start
-----------

Create a `package.json` file with

```bash
npm init
```

Install the `js-host` JavaScript library with

```bash
npm install --save js-host@0.11
```

Create a file named `host.config.js` and insert

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

Open a python shell and run

```python
from js_host.conf import settings

settings.configure(USE_MANAGER=True)
```

If everything went ok, you should see some output as the manager process spins up and then spawns a host 
which using your `host.config.js` file.

In the same python shell, run the following

```
from js_host.function import Function

hello_world = Function('hello_world')

hello_world.call()

hello_world.call(name='Foo')
```

:hatched_chick:


Settings
--------

Settings can be defined by importing `js_host.conf.settings` and calling its `configure` method
with keyword arguments matching the name of the setting that you want to define. For example

```python
from js_host.conf import settings

settings.configure(
    SOURCE_ROOT='/path/to/your/project',
    USE_MANAGER=True,
)
```

Note: if you are using this library in a Django project, please refer to the [usage in Django projects](#usage-in-django-projects) section of the documentation.


### SOURCE_ROOT

An absolute path to the directory which contains your node_modules directory.

Default: `os.getcwd()  # Your current working directory`


### CONFIG_FILE

A path to the default config file used for hosts and managers.

If the path is relative, it is appended to `SOURCE_ROOT`.

Default: `'host.config.js'`


### USE_MANAGER

Indicates that a manager should be used to spawn host instances.

DO *NOT* USE THE MANAGER IN PRODUCTION.

Default: `False`


### PATH_TO_NODE

A path to a `node` binary.

Default: `'node'`


### BIN_PATH

A path to the `js-host` binary used to control hosts and managers.

If the path is relative, it is appended to the SOURCE_ROOT setting

Default: `os.path.join('node_modules', '.bin', 'js-host')`


### FUNCTION_TIMEOUT

Indicates how many seconds `Function` objects will wait for a response before
raising exceptions.

Default: `10.0`


### CONNECT_ONCE_CONFIGURED

Indicates that once this library has been configured, it should attempt to connect to a
host.

This setting enables any config or connection errors to be raised during startup rather 
than runtime. It also enables connections to managed hosts to be preserved between 
restarts of your python process.

If you want to run multiple hosts and/or control the connection process, set this to
`False`, but be aware that managed hosts may not preserve connections when your python process 
restarts.

Default: `True`


### ROOT_URL

Overrides the root url which requests are sent to. By default, the root url is inferred from 
the config that the host generates from your config file and the js-host defaults.

If you want to route requests manually to a host, set it to a string such as 
`'http://127.0.0.1:9009'`.

Default: `None`


### VERBOSITY

Indicates how much information the host should print the terminal. By default the library
will print to the terminal whenever processes are started or connected to.

If you want to suppress all output, set it to `js_host.verbosity.SILENT`.

Default: `js_host.verbosity.PROCESS_START`


Usage in Django projects
------------------------

Due to some quirks in how Django's configuration layer works, there are a few 
[helpers](https://github.com/markfinger/optional-django) provided to integrate this library 
into a Django project.

Rather than defining settings by using `js_host.conf.settings.configure(...)`, you should place 
them into a dictionary named `JS_HOST` in your settings file and add `js_host` to your 
`INSTALLED_APPS` setting. For example

```python
INSTALLED_APPS = (
    # ...
    'js_host',
)

JS_HOST = {
    'SOURCE_ROOT': '/path/to/your/project',
    'USE_MANAGER': DEBUG,
}
```

Once django has initialized, it will trigger a phase in which `js_host` introspects django and 
then continues with the normal startup.


Usage in development
--------------------

In development, you can take advantage of the manager process to abstract away the overhead of 
starting and stopping processes. To use a manager to spawn hosts, set the `USE_MANAGER` setting
to `True`.

If you are writing functions that are on a host, you are recommended to start hosts manually, as 
it will provide more immediate feedback, as well as easier control of a process. To start a host 
manually, refer to [js-host's CLI usage](https://github.com/markfinger/js-host#cli-usage).


Usage in production
-------------------

In a production environment, you are strongly recommended to **not** use the manager. 
Ensure that the `USE_MANAGER` setting is set to `False` before you start your python process.

In a production environment, you should run your hosts under a supervisor system, such as
[supervisor](http://supervisord.org/) or [PM2](https://github.com/Unitech/pm2). You can refer 
to [js-host's CLI usage](https://github.com/markfinger/js-host#cli-usage) for the necessary 
incantation to spin up a process. It will generally boil down to something like

```bash
node_modules/.bin/js-host host.config.js
```


### Logging

By default, js-host instances will only write their logs to stdout and stderr. To log to files,
refer to js-host's [documentation on logging](https://github.com/markfinger/js-host#logging).


### Caching

js-host does not have its own caching layer, but an upstream caching layer can be implemented 
easily. All communication between the python processes and the js-host processes is performed 
via HTTP, so placing a reverse proxy such as [varnish](https://www.varnish-cache.org/) between 
the two can massively boost the performance of your requests.

By default, the python layer will infer a host's url from the host's config. If you want to route
all requests through another address, define the `ROOT_URL` setting. For example

```python
js_host.conf.settings.configure(
    # ...
    ROOT_URL='http://127.0.0.1:8000',
)
```

The python layer will now send all requests through `http://127.0.0.1:8000`, rather than connecting
directly to the host.


#### Caching requests

Requests are sent to hosts according to js-host's 
[endpoint definition](https://github.com/markfinger/js-host#endpoints).

When the python layer sends requests to functions, it appends a `hash` paramater to the url 
which is a `sha1` hash of the serialized data sent to the function. For example, a request to a 
function named `hello_world` with the data `{'foo': 'bar'}` will be sent as:

```
POST: /function/hello_world?hash=bc4919c6adf7168088eaea06e27a5b23f0f9f9da
```

This url convention enables you to easily cache a specific function's output by the data that 
was sent in.


API
---


### Function

`js_host.function.Function` objects enable you to pass data from your python process to a JavaScript 
environment. Functions must be instantiated with a string which matches a name specified in your config 
file.

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

```python
from js_host.function import Function

greeter = Function('greeter')

greeter.call()  # returns 'Hello'

double = Function('double')

double.call(number=20)  # returns '40'

double.call()  # raises a error 'No number was provided'
```

Keyword arguments provided to `call` are passed to the host as JSON. The host deserializes the
data sent, and then passes the data to your function as its first argument. The second argument 
to your function is a callback which allows you to pass data back to the python process.

Your functions can complete their task either synchronously or asynchronously. Once the callback 
has been called, the host assumes that the function has completed and sends a response back to 
the Python process.

For more information on the API and behaviour of functions, refer to the js-host's
[documentation on functions](https://github.com/markfinger/js-host#functions).


### JSHost

`JSHost` objects read in your config files and act as bridges to JavaScript environments generated
from your config files.

If you want to introspect a host, there are some utils provided

```python
# Import the host generated from the values in `js_host.conf.settings`
from js_host.host import host

# An absolute path to the node binary used to run hosts
host.path_to_node

# An absolute path to the `js-host` library used
host.get_path_to_bin()

# Returns an absolute path to the config file used by the host
host.get_path_to_config_file()

# Returns a URL which points to the location of the host on your network
host.get_url()

# Returns a dict containing information that the host reported during startup
host.get_status()

# Connects to a running host, requests information about it, and returns the data as a dict
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

# An absolute path to a file that the host writes its logs to
host.logfile

# Connect to the manager and ask it to spawn a new host using your config file
host.start()

# Connect to the manager and ask it to stop the host
host.stop()

# Connect to the manager and ask it to restart the host
host.restart()
```

### JSHostManager

`js_host.manager.JSHostManager` objects provide an interface to a detached process which runs 
on your local network and can spawn [js-host](https://github.com/markfinger/js-host) instances on 
demand.

The primary benefit of using a manager is that it abstracts away the bother of spawning a host 
manually. During development, your primary goal is to build things - issues regarding stability
and logging should be left to production environments.

To allow a manager to spawn instances automatically, set the `USE_MANAGER` setting to `True`.

If you writting functions to be used on hosts you are recommended not to use a manager. Instead
you should manually start hosts by referring to 
[js-host's CLI usage](https://github.com/markfinger/js-host#cli-usage).

Note: managers should only be used in development environments. Do **not** use the manager in 
production. Please refer to the [usage in production](#usage-in-production) section before 
configuring your production environment.


#### Under the hood

Managers are spun up via a child process of your python process. The child process blocks the python
process until the manager has been spawned in a third process which is completely detached from
your python process. Using a detached process allows the manager and its hosts to persist even 
when your python process has restarted or exited.

Once a manager is running, it starts listening for incoming requests which indicate that your
python process wants it to spawn a new js-host using a particular config file. Once the new 
instance has been spawned, the python process asks the manager to register a new connection 
to the host.

When your python process exits, it quickly sends a disconnect signal to the manager, notifying
the manager that any hosts spawned by your python process are no longer required. When a 
spawned host no longer has ony open connections, the manager will wait for 5 seconds for 
any new connections to be opened. If the time period expires and no new connections have been
opened, the manager will stop the host's process.

This connect/disconnect method enables your python process to hook in to persistent JS
environments which survive even when your python process has restarted. Maintaining persistent
environments enables you to integrate JS technologies which have a high startup cost that should 
only be incurred once. A typical use-case where this optimisation provides massive performance 
improvements is integrating a compiler - such as webpack or browserify - which have a sizable 
startup overhead as they parse all of your files.

When all of a manager's hosts have been disconnected and stopped, the manager will stop its own 
process. This enables the manager to clean up after itself, and prevents rogue processes from
running in the background.


#### Quirks

Be aware that managers introduce some quirks that you should be aware of:

- Managers and hosts are pooled based on the path to your config file. If you open a python shell 
  which triggers a connection to a host, the manager will not stop the host until your shell has 
  exited.

  If you are running a server and a python shell which have both connected to the same host, the 
  manager will not stop the host until both processes have exited.
- Managed hosts can persist after their config file has changed.
  
  To force a restart, call the `restart` method of a managed `JSHost` instance. For example
  ```python
  from js_host.host import host
  host.restart()
  ```
- Managers and managed hosts run in processes detached from your shell, which can make it difficult 
  to inspect their output streams.

  To provide some measure of introspection, managed hosts write their output to logfiles which are 
  stored in your temporary directory. The `logfile` attribute of a `JSHost` instance provides an 
  absolute path to the file. For example
  ```python
  from js_host.host import host
  print(host.logfile)
  ```
- If a managed host encounters an unhandled exception, the host will crash and the python process 
  will raise errors until you the host is respawned. By design, hosts will not respawn until you
  have restarted the python process.

  Preventing automatic respawning of crashed hosts simply hides the underlying issue, and makes it
  difficult to reason about a system's state.
  
  If a crash is detected, exceptions will be raised indicating that you should consult the host's
  logfile to inspect the stack traces produced during the unhandled exception.


#### Issues

Be aware that managers have some identified issues:

- Managers and managed hosts are only compatible with OSX and *nix systems. This issue is tracked 
  in [js-host#7](markfinger/js-host#7)


Running the tests
-----------------

```bash
pip install -r requirements.txt
cd tests
npm install
cd ..
./runtests.sh
```
