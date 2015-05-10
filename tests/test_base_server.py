import unittest
from js_host.base_server import BaseServer
from js_host.bin import read_status_from_config_file
from .settings import ConfigFiles


class TestBaseServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class BaseServerSubclass(BaseServer):
            expected_type_name = 'Host'

        cls.BaseServerSubclass = BaseServerSubclass

        cls.status = read_status_from_config_file(ConfigFiles.BASE_SERVER)
        cls.server = cls.BaseServerSubclass(cls.status, config_file=ConfigFiles.BASE_SERVER)

    def test_is_instantiated_properly(self):
        self.assertEqual(self.server.expected_type_name, 'Host')
        self.assertFalse(self.server.has_connected)
        self.assertEqual(self.server.config_file, ConfigFiles.BASE_SERVER)
        self.assertIsNotNone(self.server.status)
        self.assertIsInstance(self.server.status, dict)
        self.assertEqual(self.server.status, self.status)
        self.assertIsNone(self.server.root_url)

    def test_can_produce_url_to_itself(self):
        self.assertEqual(self.server.get_url(), 'http://127.0.0.1:9876')
        self.assertEqual(self.server.get_url('some/endpoint'), 'http://127.0.0.1:9876/some/endpoint')

    def test_can_use_an_override_when_generating_urls(self):
        self.assertIsNone(self.server.root_url)
        self.server.root_url = 'http://123.456.789.0:1234'
        self.assertEqual(self.server.get_url(), 'http://123.456.789.0:1234')
        self.assertEqual(self.server.get_url('some/endpoint'), 'http://123.456.789.0:1234/some/endpoint')
        self.server.root_url = None

    def test_can_request_status_safely(self):
        self.assertIsNone(self.server.request_status())

    def test_can_check_if_running_safely(self):
        self.assertFalse(self.server.is_running())