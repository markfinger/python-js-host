# python-js-host

[![Build Status](https://travis-ci.org/markfinger/python-js-host.svg?branch=master)](https://travis-ci.org/markfinger/python-js-host)

Provides the plumbing to performantly pass data from Python to JavaScript, and receive the generated output.

There are a variety of libraries which provide access to JS engines, [PyExecJS](https://github.com/doloopwhile/PyExecJS) et al, but they only provide basic functionality, 
suffer performance problems, and require you to generate strings of JS which are evaluated. 

[js-host](https://github.com/markfinger/js-host) avoids these issues by providing a performant and 
persistent JS environment which responds over the network. Behind the scenes, the python layer 
provides the bindings necessary to connect to a running environment, call specific functions and 
receive their output.

To reduce the pains of integrating another environment into your development stack, a 
[manager process](#jshostmanager) is provided to automatically spawn JS hosts which run in 
the background and persist only as long as your python process is running.


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

Do **not** use the manager in production, it exists purely to solve issues relating
to the typical development environment. Please refer to the 
[usage in production](#usage-in-production) section before setting up a production
environment.

Managers exist to solve the following problems:

- Many of the typical JS functions involve processes which have an initial overhead,
  but are performant after the first run, compilers are the usual example. If a host
  runs as a child process of the python process, it will have to restart whenever the
  python process does. Given the frequent restarts of python development servers,
  the aforementioned issues of a compiler's inital overhead become painful very quickly.
- If you run the node process as a detached child, the performance is better, but this 
  introduces additional overheads as you need to ensure that the process is inevitably 
  stopped. The manager does this for you automatically - once your python process has 
  stopped running, the manager waits for a small time period and then stops the 
  host as well. When the manager is no longer responsible for any hosts, it will stop 
  its own process.
- Using a manager removes the need for staff and other developers to run yet-another-command 
  when starting or running a project. Removing unwanted overhead makes everyone's life 
  a lot happier.

Managers have some identified issues:

- Managers and managed hosts do not provide a means to inspect their stdout or stderr,
  which can complicate debugging as you rely on the host's response cycle to introspect
  an environment. [This issue is tracked in #3](markfinger/python-js-host#3)
- Managed hosts will persist even when their config file has changed. To force a restart 
  of a managed host, call `restart` on a `JSHost` instance. For example:
  ```
  from js_host.host import host
  
  host.restart()
  ```

If you wish to avoid these issues, you are recommended to set the `USE_MANGER` setting
to `False`, and start hosts manually.


Settings
--------


Django integration
------------------


Usage in development
--------------------


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
