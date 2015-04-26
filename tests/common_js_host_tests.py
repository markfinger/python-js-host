import os
import unittest
import json
from js_host.base_server import BaseServer
from js_host.exceptions import JSFunctionError, JSFunctionTimeout
from js_host.conf import settings


class CommonJSHostTests(unittest.TestCase):
    """
    A common test suite to be run over JSHost and any subclasses
    """
    # Subclasses should set this to True, to ensure the test runner
    # starts those tests
    __test__ = False

    host = None
    common_js_host_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'common_js_host_tests.host.config.js')

    def test_inherits_from_base_server(self):
        self.assertIsInstance(self.host, BaseServer)

    def test_is_instantiated_properly(self):
        self.assertEqual(self.host.type_name, 'Host')
        self.assertEqual(self.host.path_to_node, settings.PATH_TO_NODE)
        self.assertEqual(self.host.source_root, settings.SOURCE_ROOT)
        self.assertIsNotNone(self.host.config)
        self.assertIsInstance(self.host.config, dict)
        self.assertEqual(self.host.config_file, self.common_js_host_config_file)

    def test_is_running(self):
        self.assertTrue(self.host.is_running())

    def test_can_handle_errors(self):
        self.assertRaises(JSFunctionError, self.host.call_function, 'echo')

        self.assertRaises(JSFunctionError, self.host.call_function, 'async_echo')

        self.assertRaises(JSFunctionError, self.host.call_function, 'error')

        try:
            self.host.call_function('error')
            raise Exception('A JSFunctionError should have been raised before this line')
        except JSFunctionError as e:
            self.assertIn('Hello from error function', str(e))

    def test_can_cache_content(self):
        res = self.host.call_function('echo', data=json.dumps({'echo': 'test1'}), key='foo')
        self.assertEqual(res.text, 'test1')

        res = self.host.call_function('echo', data=json.dumps({'echo': 'test2'}), key='bar')
        self.assertEqual(res.text, 'test2')

        res = self.host.call_function('echo', data=json.dumps({'echo': 'test3'}), key='foo')
        self.assertEqual(res.text, 'test1')

        res = self.host.call_function('echo_data', data=json.dumps({'echo': 'test4'}), key='foo')
        self.assertEqual(json.loads(res.text), {'echo': 'test4'})

        res = self.host.call_function('echo_data', data=json.dumps({'echo': 'test5'}), key='bar')
        self.assertEqual(json.loads(res.text), {'echo': 'test5'})

        res = self.host.call_function('echo_data', data=json.dumps({'echo': 'test6'}), key='foo')
        self.assertEqual(json.loads(res.text), {'echo': 'test4'})

        res = self.host.call_function('async_echo', data=json.dumps({'echo': 'test7'}), key='foo')
        self.assertEqual(res.text, 'test7')

        res = self.host.call_function('async_echo', data=json.dumps({'echo': 'test8'}), key='bar')
        self.assertEqual(res.text, 'test8')

        res = self.host.call_function('async_echo', data=json.dumps({'echo': 'test9'}), key='foo')
        self.assertEqual(res.text, 'test7')

    def test_can_handle_function_timeouts(self):
        self.assertRaises(
            JSFunctionTimeout,
            self.host.call_function,
            'async_echo',
            timeout=0.2
        )

        res = self.host.call_function('echo', data=json.dumps({'echo': 'bar'}), timeout=0.2)
        self.assertEqual(res.text, 'bar')