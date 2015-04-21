import os
import unittest
import json
from service_host.base_server import BaseServer
from service_host.exceptions import ServiceError, ServiceTimeout
from service_host.conf import settings


class CommonServiceHostTests(unittest.TestCase):
    """
    A common test suite to be run over ServiceHost and any subclasses
    """
    # Subclasses should set this to True, to ensure the test runner
    # starts those tests
    __test__ = False

    host = None
    common_service_host_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'common_service_host_tests.services.config.js')

    def test_inherits_from_base_server(self):
        self.assertIsInstance(self.host, BaseServer)

    def test_is_instantiated_properly(self):
        self.assertEqual(self.host.type_name, 'Host')
        self.assertEqual(self.host.path_to_node, settings.PATH_TO_NODE)
        self.assertEqual(self.host.path_to_node_modules, settings.PATH_TO_NODE_MODULES)
        self.assertIsNotNone(self.host.config)
        self.assertIsInstance(self.host.config, dict)
        self.assertEqual(self.host.config_file, self.common_service_host_config_file)

    def test_is_running(self):
        self.assertTrue(self.host.is_running())

    def test_can_handle_errors(self):
        self.assertRaises(ServiceError, self.host.send_request_to_service, 'echo')

        self.assertRaises(ServiceError, self.host.send_request_to_service, 'async_echo')

        self.assertRaises(ServiceError, self.host.send_request_to_service, 'error')

        try:
            self.host.send_request_to_service('error')
            raise Exception('A ServiceError should have been raised before this line')
        except ServiceError as e:
            self.assertIn('Hello from error service', str(e))

    def test_can_cache_content(self):
        res = self.host.send_request_to_service('echo', data=json.dumps({'echo': 'test1'}), cache_key='foo')
        self.assertEqual(res.text, 'test1')

        res = self.host.send_request_to_service('echo', data=json.dumps({'echo': 'test2'}), cache_key='bar')
        self.assertEqual(res.text, 'test2')

        res = self.host.send_request_to_service('echo', data=json.dumps({'echo': 'test3'}), cache_key='foo')
        self.assertEqual(res.text, 'test1')

        res = self.host.send_request_to_service('echo_data', data=json.dumps({'echo': 'test4'}), cache_key='foo')
        self.assertEqual(json.loads(res.text), {'echo': 'test4'})

        res = self.host.send_request_to_service('echo_data', data=json.dumps({'echo': 'test5'}), cache_key='bar')
        self.assertEqual(json.loads(res.text), {'echo': 'test5'})

        res = self.host.send_request_to_service('echo_data', data=json.dumps({'echo': 'test6'}), cache_key='foo')
        self.assertEqual(json.loads(res.text), {'echo': 'test4'})

        res = self.host.send_request_to_service('async_echo', data=json.dumps({'echo': 'test7'}), cache_key='foo')
        self.assertEqual(res.text, 'test7')

        res = self.host.send_request_to_service('async_echo', data=json.dumps({'echo': 'test8'}), cache_key='bar')
        self.assertEqual(res.text, 'test8')

        res = self.host.send_request_to_service('async_echo', data=json.dumps({'echo': 'test9'}), cache_key='foo')
        self.assertEqual(res.text, 'test7')

    def test_can_handle_service_timeouts(self):
        self.assertRaises(
            ServiceTimeout,
            self.host.send_request_to_service,
            'async_echo',
            timeout=0.2
        )

        res = self.host.send_request_to_service('echo', data=json.dumps({'echo': 'bar'}), timeout=0.2)
        self.assertEqual(res.text, 'bar')