import json
import os
import unittest
from js_host.exceptions import ConfigError, JSFunctionError
from js_host.function import Function
from js_host.conf import settings
from js_host.js_host import JSHost
from js_host.host import host

no_functions_host_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'no_functions.host.config.js')


class TestFunctions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.echo = Function('echo')
        cls.echo_data = Function('echo_data')
        cls.async_echo = Function('async_echo')
        cls.error = Function('error')

    def test_is_instantiated_properly(self):
        function = Function(name='foo')

        self.assertEqual(function.name, 'foo')
        self.assertEqual(function.host, None)
        self.assertEqual(function.cacheable, True)

    def test_name_is_required(self):
        self.assertRaises(ConfigError, Function)

    def test_host_is_bound_lazily(self):
        function = Function(name='test')
        self.assertIsNone(function.host)
        self.assertEqual(function.get_host(), host)
        self.assertEqual(function.host, host)

    def test_get_name(self):
        self.assertEqual(self.echo.get_name(), self.echo.name)

    def test_get_config_validates_the_host_config(self):
        class Test(Function):
            name = 'test'
        function = Test()

        function.host = JSHost(config_file=no_functions_host_config_file)

        self.assertIsInstance(function.host.config['functions'], list)
        self.assertEqual(len(function.host.config['functions']), 0)

        self.assertRaises(ConfigError, function.get_config)

        function.host.config['functions'].append({'name': 'test', 'cache': False})

        self.assertEqual(function.get_config(), {'name': 'test', 'cache': False})

    def test_generate_cache_key(self):
        self.assertEqual(
            self.echo.generate_cache_key('foo', None),
            '0beec7b5ea3f0fdbc95d0dd47f3c5bc275da8a33',
        )

    def test_serialize_data(self):
        self.assertEqual(
            self.echo.serialize_data({'foo': 'bar', 'woz': [1, 2, 3]}),
            json.dumps({'foo': 'bar', 'woz': [1, 2, 3]}),
        )

    def test_is_cacheable(self):
        _CACHE = settings.CACHE

        settings._unlock()
        settings.CACHE = True

        class Uncacheable(Function):
            name = 'echo'
            cacheable = False
        uncacheable = Uncacheable()

        self.assertFalse(uncacheable.is_cacheable())

        uncacheable.cacheable = True
        self.assertTrue(uncacheable.is_cacheable())

        uncacheable.config['cache'] = False
        self.assertFalse(uncacheable.is_cacheable())

        uncacheable.config['cache'] = True
        self.assertTrue(uncacheable.is_cacheable())

        settings.CACHE = False
        self.assertFalse(uncacheable.is_cacheable())

        # Revert the setting
        settings.CACHE = _CACHE
        settings._lock()

    def test_send_request(self):
        self.assertEqual(self.echo.send_request(echo='test').text, 'test')
        self.assertEqual(self.echo_data.send_request().text, '{}')
        self.assertEqual(
            json.loads(self.echo_data.send_request(foo=1, bar=[2, 3, {'woz': 4}]).text),
            {'foo': 1, 'bar': [2, 3, {'woz': 4}]}
        )
        self.assertEqual(self.async_echo.send_request(echo='foo').text, 'foo')

    def test_call(self):
        self.assertEqual(self.echo.call(echo='test'), 'test')
        self.assertEqual(self.echo_data.call(), '{}')
        self.assertEqual(
            json.loads(self.echo_data.call(foo=1, bar=[2, 3, {'woz': 4}])),
            {'foo': 1, 'bar': [2, 3, {'woz': 4}]}
        )
        self.assertEqual(self.async_echo.call(echo='foo'), 'foo')

    def test_500_errors_are_raised_as_Function_errors(self):
        self.assertRaises(JSFunctionError, self.error.call)
        self.assertRaises(JSFunctionError, self.echo.call)
        self.assertRaises(JSFunctionError, self.echo.call, _echo='test')
        self.assertRaises(JSFunctionError, self.echo.call, foo='test')