import os
import unittest
from service_host.base_server import BaseServer
from service_host.exceptions import ConfigError
from service_host.conf import settings

missing_config_file = os.path.join(os.path.dirname(__file__), 'config_files', '__non_existent_file__')
empty_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'empty.services.config.js')
base_server_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'test_base_server.services.config.js')


class TestBaseServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class BaseServerSubclass(BaseServer):
            type_name = 'Test'

        cls.BaseServerSubclass = BaseServerSubclass

        cls.server = cls.BaseServerSubclass(
            path_to_node=settings.PATH_TO_NODE,
            path_to_node_modules=settings.PATH_TO_NODE_MODULES,
            config_file=base_server_config_file
        )

    def test_is_instantiated_properly(self):
        self.assertEqual(self.server.type_name, 'Test')
        self.assertFalse(self.server.has_connected)
        self.assertEqual(self.server.config_file, base_server_config_file)
        self.assertEqual(self.server.path_to_node, settings.PATH_TO_NODE)
        self.assertEqual(self.server.path_to_node_modules, settings.PATH_TO_NODE_MODULES)
        self.assertIsNotNone(self.server.config)

    def test_can_read_in_config(self):
        self.assertEqual(self.server.get_config(), self.server.config)
        self.assertEqual(self.server.config['address'], '127.0.0.1')
        self.assertEqual(self.server.config['port'], 9876)
        self.assertEqual(self.server.config['someUnexpectedProp'], 'foo')

    def test_can_produce_url_to_itself(self):
        self.assertEqual(self.server.get_url(), 'http://127.0.0.1:9876')
        self.assertEqual(self.server.get_url('some/endpoint'), 'http://127.0.0.1:9876/some/endpoint')

    def test_can_request_type_name_safely(self):
        self.assertIsNone(self.server.request_type_name())

    def test_can_check_if_running_safely(self):
        self.assertFalse(self.server.is_running())

    def test_raises_an_error_if_a_config_file_does_not_exist(self):
        self.assertRaises(
            ConfigError,
            self.BaseServerSubclass,
            path_to_node=settings.PATH_TO_NODE,
            path_to_node_modules=settings.PATH_TO_NODE_MODULES,
            config_file=missing_config_file,
        )

    def test_raises_an_error_if_a_config_file_does_not_export_an_object(self):
        self.assertRaises(
            ConfigError,
            self.BaseServerSubclass,
            path_to_node=settings.PATH_TO_NODE,
            path_to_node_modules=settings.PATH_TO_NODE_MODULES,
            config_file=empty_config_file,
        )

    def test_can_validate_config(self):
        self.assertRaises(ConfigError, self.server.validate_config, None)
        self.assertRaises(ConfigError, self.server.validate_config, {})
        self.assertRaises(ConfigError, self.server.validate_config, {'address': True})
        self.assertRaises(ConfigError, self.server.validate_config, {'port': True})
        self.server.validate_config({'address': True, 'port': True})