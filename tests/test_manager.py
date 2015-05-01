import json
import os
import unittest
import time
from js_host.base_server import BaseServer
from js_host.exceptions import ConnectionError
from js_host.js_host import JSHost
from js_host.manager import JSHostManager
from js_host.conf import settings

manager_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'test_manager.host.config.js')
manager_lifecycle_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'test_manager_lifecycle.host.config.js')


class TestManager(unittest.TestCase):
    manager = None

    @classmethod
    def setUpClass(cls):
        cls.manager = JSHostManager(config_file=manager_config_file)
        cls.manager.start()
        cls.manager.connect()

    @classmethod
    def tearDownClass(cls):
        cls.manager.stop()

    def test_inherits_from_base_server(self):
        self.assertIsInstance(self.manager, BaseServer)

    def test_is_instantiated_properly(self):
        self.assertEqual(self.manager.expected_type_name, 'Manager')
        self.assertEqual(self.manager.config_file, manager_config_file)
        self.assertEqual(self.manager.path_to_node, settings.PATH_TO_NODE)
        self.assertEqual(self.manager.source_root, settings.SOURCE_ROOT)
        self.assertIsNotNone(self.manager.status)
        self.assertIsInstance(self.manager.status, dict)

    def test_can_read_in_config(self):
        self.assertEqual(self.manager.get_config(), self.manager.status['config'])
        self.assertEqual(self.manager.get_config()['address'], '127.0.0.1')
        self.assertEqual(self.manager.get_config()['port'], 45678)

    def test_can_produce_url_to_itself(self):
        self.assertEqual(self.manager.get_url(), 'http://127.0.0.1:45678')
        self.assertEqual(self.manager.get_url('some/endpoint'), 'http://127.0.0.1:45678/some/endpoint')

    def test_is_running(self):
        self.assertTrue(self.manager.is_running())

    def test_accepts_requests(self):
        res = self.manager.send_request('status')
        self.assertEqual(
            json.loads(res.text),
            self.manager.get_status(),
        )

    def test_manager_lifecycle(self):
        manager = JSHostManager(config_file=manager_lifecycle_config_file)

        self.assertEqual(manager.get_config()['port'], 34567)

        self.assertRaises(ConnectionError, manager.connect)

        self.assertFalse(manager.is_running())

        self.assertRaises(ConnectionError, manager.connect)

        manager.start()

        manager.connect()

        self.assertTrue(manager.is_running())

        manager.stop()

        self.assertFalse(manager.is_running())

        self.assertRaises(ConnectionError, manager.connect)

    def test_managers_stop_shortly_after_the_last_host_has_disconnected(self):
        manager = JSHostManager(config_file=manager_lifecycle_config_file)

        manager.start()
        manager.connect()

        host1 = JSHost(manager=manager)
        host1.start()
        host1.connect()

        self.assertTrue(host1.is_running())

        host2 = JSHost(manager=manager, config_file=manager_config_file)
        host2.start()
        host2.connect()

        self.assertNotEqual(host1.get_config()['port'], host2.get_config()['port'])

        self.assertTrue(host2.is_running())

        host1.disconnect()
        time.sleep(0.2)

        self.assertFalse(host1.is_running())
        self.assertTrue(manager.is_running())

        data = manager.fetch_host_status(host1.get_path_to_config_file())
        self.assertFalse(data['started'])

        self.assertTrue(manager.is_running())

        host2.disconnect()
        time.sleep(0.2)

        self.assertFalse(host2.is_running())
        self.assertFalse(manager.is_running())