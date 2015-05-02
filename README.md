# python-js-host

[![Build Status](https://travis-ci.org/markfinger/python-js-host.svg?branch=master)](https://travis-ci.org/markfinger/python-js-host)

Python bindings to a performant JavaScript environment.

There are a variety of libraries which provide access to JS engines, PyExecJS et al, but they only provide 
basic functionality, suffer performance problems, and introduce setup overhead. Rather than provide low-level 
hooks to evaluate JavaScript, this library hooks in to an
[opinionated JavaScript layer](https://github.com/markfinger/js-host) which runs persistent and performant 
environments built for easy configuration.

In development, a [manager process](#jshostmanager) is provided to reduce your integration overheads. The 
process runs in the background and spawns environments which your python process uses. Once your python 
process no longer needs the environment, the manager handles the overhead of stopping the environment and
cleaning up after itself.

In production, the same codebase is used to connect to environments which you spawn and control manually.


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


API
---


### Function

`Function` objects enable you to connect to a running JS host and request the output of the function
matching the specified name.

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

Note: any value that your function returns with the `return` keyword will be ignored by the host. 
The host will only pay attention to values which are passed to the callback. The `return` statements 
in your function should only be used for controlling the flow of logic.

For more information on the API and behaviour of functions, refer to the 
[js-host documentation on functions](https://github.com/markfinger/js-host#functions).


### JSHost

`JSHost` objects read in your config files and connect to JS environments to call functions.
Behind the scenes, `Function` objects use JSHosts as bridges to connect to the JS environments.

In development, you can typically rely on the manager to handle starting and stopping hosts.
If you do need to interact or introspect a host, there are some utils provided to assist you

```
from js_host.js_host import JSHost

host = JSHost('/path/to/host.config.js')

host.get_url()  # returns a URL which points to the location of the host on your network

host.get_config()  # returns a dict created from converting your config file to JSON

host.is_running()  # Returns True/False if a host process is running at the expected url

host.connect()  # Connect to an environment and validate that it matches your config
```

If you are using the `JSHostManager` to control your hosts, the following utils 
are also available on `JSHost` objects

```python
# the JSHostManager instance that the host uses
host.manager

# If the host is running, this exits immediately
# If the host is not running, this blocks until the manager has started the host
host.start()

# If the host is running, this blocks until the manager has stopped the host
# If the host is not running, this exits immediately
host.stop()

# Note: if you stop the last host on a manager, the manager will stop as well.
# You can prevent this by calling...
host.stop(stop_manager_if_last=False)

# Blocks until the process has completely restarted
host.restart()
```

### JSHostManager

`JSHostManager` objects provide an interface to a detached process which runs on 
your local network and spawns [js-host](https://github.com/markfinger/js-host) 
instances on demand.

Note: do **not** use the manager in production, it only aims to solve issues relating
to the typical development environment. Please refer to the 
[usage in production](#usage-in-production) section before setting up a production
environment.

Managers solve the following problems:

- Many of the typical use cases for JS functions involve processes which have an
  initial overhead, but are performant after the first run, compilers are the usual
  example. If a JS host runs as a child process of the python process, it will have
  to restart whenever the python process does. Given the frequent restarts of python
  development servers, the issue of a compiler's initial overhead becomes painful very
  quickly.
- If you run the host process as a detached child, the lack of restarts will improve 
  performance, but it introduces additional overheads as you need to ensure that the 
  process is inevitably stopped. The manager does this for you automatically. Once
  your python process has stopped running, the manager will wait for a small time 
  period and then stop the JS host as well. Once the manager is no longer responsible 
  for any hosts, it stops its own process as well.
- Using a manager removes the need for staff and other developers to run yet another command 
  when starting or running a project. Removing unwanted overhead with tools that 'just work' 
  lets everyone focus on making stuff.

Be aware that `JSHostManagers` have some identified issues:

- Managed hosts can persist after their config file has changed. To force a restart
  of a managed host, you can call the `restart` method on a `JSHost` instance.

  For example
  ```python
  # Run this after you have configured js_host.conf.settings

  from js_host.host import host
  host.restart()
  ```
- Managers and managed hosts do not provide a means to inspect their stdout or stderr.

  This can complicate debugging as you need to rely on the host's response cycle to introspect
  an environment.

  [Tracked in python-js-host#3](markfinger/python-js-host#3)
- If a managed host crashes, you will need to restart the python process to restart the
  host.

  Note: this behaviour will not change, as respawning crashed hosts hides the underlying issue.

  [Tracked in python-js-host#4](markfinger/python-js-host#4)
- Managers and managed hosts are only compatible with OSX and *nix systems.
  [Tracked in js-host#7](markfinger/js-host#7)

If you wish to avoid these issues, you are recommended to set the `USE_MANGER` setting
to `False`, and [start hosts manually](#usage-in-production).


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


### ON_EXIT_STOP_MANAGED_HOSTS_AFTER

Indicates how many milliseconds the manager will wait before stopping hosts.

When the python process exits, the manager is informed to stop the host once this
timeout has expired. If the python process is only restarting, the manager will
cancel the timeout once it has reconnected. If the python process is shutting down
for good, the manager will stop the host's process shortly.

Default:  `5 * 1000  # 5 seconds`


### VERBOSITY

Indicates how much information the host should print the terminal. By default this
will print to the terminal whenever processes are started or connected to.

If you want to suppress all output, set it to `js_host.verbosity.SILENT`.

Default: `js_host.verbosity.PROCESS_START`


### CONNECT_ONCE_CONFIGURED

Indicates that once `js_host` has been configured, it should attempt to connect to a
host.

This setting enables any config or connection errors to be raised during startup,
rather than during runtime. It also enables connections to managed hosts to be
preserved between restarts of your python process.

Default: `True`


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
the environment and configuring itself.


Usage in development
--------------------

USE_MANAGER = True
`host.restart()` to load a new config

Usage in production
-------------------

Run with `node node_modules/.bin/js-host host.config.js`

Define a unique port in your `host.config.js`

Ensure that `USE_MANAGER` is false.

If you want, configure a `logger` in your `host.config.js`.


Debugging a host
----------------

```bash
node debug node_modules/.bin/js-host host.config.js
```


Running the tests
-----------------

```bash
mkvirtualenv js-host
pip install -r requirements.txt
./runtests.sh
```
