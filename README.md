# python-js-host

[![Build Status](https://travis-ci.org/markfinger/python-js-host.svg?branch=master)](https://travis-ci.org/markfinger/python-js-host)

Provides the plumbing to performantly pass data from Python to JavaScript, and receive the generated output.

There are a variety of libraries which provide access to JS engines, PyExecJS et al, but they only
provide basic functionality, suffer performance problems, and require you to generate strings of 
JS which are evaluated. 

The [js-host](https://github.com/markfinger/js-host) package avoids these issues by providing a performant 
and persistent JS environment with easy access to the entire node & io.js ecosystem.

This python layer provides the bindings necessary to connect to a running environment, call specific 
functions and receive their output.

To reduce the pains of integrating yet another technology into your development stack, a 
[manager process](#jshostmanager) is provided as a dev tool. The manager runs in the background
and spawn JS hosts which persist only as long as your python process is running.


Installation
------------

```bash
pip install js-host
```


Dependencies
------------

[node](nodejs.org) or [io.js](https://iojs.org/)

[npm](https://www.npmjs.com/)


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

Create a file named `hello_world.py` and insert the following

```python
import os
from js_host.conf import settings as js_host_settings
from js_host.function import Function

js_host_settings.configure(
  SOURCE_ROOT=os.path.dirname(os.path.abspath(__file__)),
  USE_MANAGER=True,
)

hello_world = Function('hello_world')

print(hello_world.call())

print(hello_world.call(name='Foo'))
```

Run the `hello_world.py` file

```bash
python hello_world.py
```

If everything went ok, you should see some output as the JS host starts and then the following two lines

```
Hello, World!
Hello, Foo!
```

API
---


### Function

`Function` objects enable you to connect to a running JS host and request the output of a function which 
matches a specified name.

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

- Many of the typical JS functions involve processes which have an initial overhead,
  but are performant after the first run, compilers are the usual example. If a host
  runs as a child process of the python process, it will have to restart whenever the
  python process does. Given the frequent restarts of python development servers,
  the issue of a compiler's inital overhead becomes painful very quickly.
- If you run the host process as a detached child, the lack of restarts will improve 
  performance, but it introduces additional overheads as you need to ensure that the 
  process is inevitably stopped. The manager does this for you automatically - once 
  your python process has stopped running, the manager will wait for a small time 
  period and then stop the JS host as well. Once the manager is no longer responsible 
  for any hosts, it stops its own process as well.
- Using a manager removes the need for staff and other developers to run yet another command 
  when starting or running a project. Removing unwanted overhead with tools that 'just work' 
  lets everyone focus on making cool stuff.

Be aware that managers have some identified issues:

- Managed hosts can persist after their config file has changed. To force a restart of a 
  managed host, call `restart` on a `JSHost` instance. For example:
  ```
  from js_host.host import host
  
  host.restart()
  ```
- Managers and managed hosts do not currently provide a means to inspect their stdout or 
  stderr. This can complicate debugging as you need to rely on the host's response cycle 
  to introspect an environment. [This issue is tracked in #3](markfinger/python-js-host#3)

If you wish to avoid these issues, you are recommended to set the `USE_MANGER` setting
to `False`, and start hosts manually.


Settings
--------

```python
PATH_TO_NODE = 'node'

# An absolute path to the directory which contains your node_modules directory
SOURCE_ROOT = None

# A path to the binary used to control hosts and managers.
# If the path is relative, it is appended to the SOURCE_ROOT setting
BIN_PATH = os.path.join('node_modules', '.bin', 'js-host')

# A path to the default config file used for hosts and managers.
# If the path is relative, it is appended to the SOURCE_ROOT setting.
CONFIG_FILE = 'host.config.js'

# If True, the host will cache the output of the functions until it expires.
# This can be overridden on functions by adding `cachable = False` to the
# subclass of `Function`, or by adding `cache: false` to the config file's
# object for that particular function
CACHE = False

# By default this will print to the terminal whenever processes are started or
# connected to. If you want to suppress all output, set it to
# `js_host.conf.Verbosity.SILENT`
VERBOSITY = Verbosity.PROCESS_START

FUNCTION_TIMEOUT = 10.0

# Indicates that a manager should be used to spawn host instances
# DO *NOT* USE THE MANAGER IN PRODUCTION
USE_MANAGER = False

# When the python process exits, the manager is informed to stop the host once this
# timeout has expired. If the python process is only restarting, the manager will
# cancel the timeout once it has reconnected. If the python process is shutting down
# for good, the manager will stop the host's process shortly.
ON_EXIT_STOP_MANAGED_HOSTS_AFTER = 10 * 1000  # 10 seconds

# Once the js host has been configured, attempt to connect. This enables any
# config or connection errors to be raised during startup, rather than runtime
CONNECT_ONCE_CONFIGURED = True
```

Django integration
------------------

settings namespace
INSTALLED_APPS to ensure the host starts/connects on startup

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
