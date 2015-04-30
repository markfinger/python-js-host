import os
import unittest
from js_host.base_server import BaseServer
from js_host.exceptions import ConfigError
from js_host.conf import settings

missing_config_file = os.path.join(os.path.dirname(__file__), 'config_files', '__non_existent_file__')
empty_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'empty.host.config.js')
base_server_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'test_base_server.host.config.js')


class TestBaseServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class BaseServerSubclass(BaseServer):
            expected_type_name = 'Host'

        cls.BaseServerSubclass = BaseServerSubclass

        cls.server = cls.BaseServerSubclass(config_file=base_server_config_file)

    def test_is_instantiated_properly(self):
        self.assertEqual(self.server.expected_type_name, 'Host')
        self.assertFalse(self.server.has_connected)
        self.assertEqual(self.server.config_file, base_server_config_file)
        self.assertEqual(self.server.path_to_node, settings.PATH_TO_NODE)
        self.assertEqual(self.server.source_root, settings.SOURCE_ROOT)
        self.assertIsNotNone(self.server.status)
        self.assertIsInstance(self.server.status, dict)

    def test_can_read_in_config(self):
        base_server_config = self.server.read_config_file(base_server_config_file)
        self.assertEqual(self.server.get_status(), base_server_config)

        self.assertEqual(self.server.get_config()['address'], '127.0.0.1')
        self.assertEqual(self.server.get_config()['port'], 9876)
        self.assertEqual(self.server.get_config()['someUnexpectedProp'], 'foo')

    def test_can_produce_url_to_itself(self):
        self.assertEqual(self.server.get_url(), 'http://127.0.0.1:9876')
        self.assertEqual(self.server.get_url('some/endpoint'), 'http://127.0.0.1:9876/some/endpoint')

    def test_can_request_status_safely(self):
        self.assertIsNone(self.server.request_status())

    def test_can_check_if_running_safely(self):
        self.assertFalse(self.server.is_running())

    def test_raises_an_error_if_a_config_file_does_not_exist(self):
        self.assertRaises(
            ConfigError,
            self.BaseServerSubclass,
            path_to_node=settings.PATH_TO_NODE,
            source_root=settings.SOURCE_ROOT,
            config_file=missing_config_file,
        )

    def test_raises_an_error_if_a_config_file_does_not_export_an_object(self):
        self.assertRaises(
            ConfigError,
            self.BaseServerSubclass,
            path_to_node=settings.PATH_TO_NODE,
            source_root=settings.SOURCE_ROOT,
            config_file=empty_config_file,
        )