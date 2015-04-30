import json
import os
import unittest
from js_host.exceptions import ConfigError, FunctionError, FunctionTimeout
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
        self.assertEqual(function.timeout, None)

    def test_name_is_required(self):
        self.assertRaises(ConfigError, Function)

    def test_host_is_bound_lazily(self):
        function = Function(name='test')
        self.assertIsNone(function.host)
        self.assertEqual(function.get_host(), host)
        self.assertEqual(function.host, host)

    def test_get_name(self):
        self.assertEqual(self.echo.get_name(), self.echo.name)

    def test_functions_validate_the_hosts_config(self):
        function = Function('test')

        function.host = JSHost(config_file=no_functions_host_config_file)

        self.assertEqual(function.host.get_config()['functions'], [])

        self.assertRaises(ConfigError, function.send_request)

        function.host.get_config()['functions'].append({'name': 'test'})

    def test_generate_key(self):
        self.assertEqual(
            self.echo.generate_key('foo', None),
            '0beec7b5ea3f0fdbc95d0dd47f3c5bc275da8a33',
        )

    def test_serialize_data(self):
        self.assertEqual(
            self.echo.serialize_data({'foo': 'bar', 'woz': [1, 2, 3]}),
            json.dumps({'foo': 'bar', 'woz': [1, 2, 3]}),
        )

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
        self.assertRaises(FunctionError, self.error.call)
        self.assertRaises(FunctionError, self.echo.call)
        self.assertRaises(FunctionError, self.echo.call, _echo='test')
        self.assertRaises(FunctionError, self.echo.call, foo='test')

        try:
            self.error.call()
            raise Exception('A FunctionError should have been raised before this line')
        except FunctionError as e:
            self.assertIn('Hello from error function', str(e))

    def test_can_raise_timeouts(self):
        async_echo = Function('async_echo')
        async_echo.timeout = 0.2

        self.assertRaises(
            FunctionTimeout,
            async_echo.call,
        )