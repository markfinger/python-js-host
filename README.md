# python-js-host

[![Build Status](https://travis-ci.org/markfinger/python-js-host.svg?branch=master)](https://travis-ci.org/markfinger/python-js-host)

Python bindings to [js-host](https://github.com/markfinger/js-host), providing a configurable JavaScript host.


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

Add a file named `host.config.js` and insert the following

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

Add a file named `hello_world.py` and insert the following

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

And run the `hello_world.py` file

```bash
python hello_world.py
```

If everything went ok, you should see some output as js-host starts and then the following two lines

```
Hello, World!
Hello, Foo!
```


Functions
---------


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

Running the tests
-----------------

```bash
mkvirtualenv js-host
pip install -r requirements.txt
./runtests.sh
```
