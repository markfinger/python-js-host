import json
import unittest
import time
from js_host.base_server import BaseServer
from js_host.exceptions import ConnectionError
from js_host.manager import JSHostManager
from js_host.conf import settings
from js_host.bin import spawn_detached_manager, spawn_managed_host, read_status_from_config_file
from .settings import ConfigFiles


class TestManager(unittest.TestCase):
    manager = None

    @classmethod
    def setUpClass(cls):
        cls.manager = spawn_detached_manager(config_file=ConfigFiles.MANAGER)

    @classmethod
    def tearDownClass(cls):
        cls.manager.stop()

    def test_inherits_from_base_server(self):
        self.assertIsInstance(self.manager, BaseServer)

    def test_is_instantiated_properly(self):
        self.assertEqual(self.manager.expected_type_name, 'Manager')
        self.assertEqual(self.manager.config_file, ConfigFiles.MANAGER)
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
        manager = JSHostManager(
            status=read_status_from_config_file(ConfigFiles.MANAGER_LIFECYCLE, extra_args=('--manager',)),
            config_file=ConfigFiles.MANAGER_LIFECYCLE
        )

        self.assertEqual(manager.get_config()['port'], 34567)

        self.assertRaises(ConnectionError, manager.connect)

        self.assertFalse(manager.is_running())

        self.assertRaises(ConnectionError, manager.connect)

        # Spawn the process in the background
        spawn_detached_manager(config_file=ConfigFiles.MANAGER_LIFECYCLE)

        self.assertTrue(manager.is_running())

        manager.connect()

        self.assertTrue(manager.is_running())

        manager.stop()

        self.assertRaises(ConnectionError, manager.connect)

        self.assertFalse(manager.is_running())

    def test_managers_stop_shortly_after_the_last_host_has_disconnected(self):
        manager = spawn_detached_manager(config_file=ConfigFiles.MANAGER_LIFECYCLE)

        host1 = spawn_managed_host(ConfigFiles.MANAGER_LIFECYCLE, manager)

        self.assertTrue(host1.is_running())

        host2 = spawn_managed_host(ConfigFiles.MANAGER, manager)

        self.assertNotEqual(host1.get_config()['port'], host2.get_config()['port'])

        self.assertTrue(host2.is_running())

        host1.disconnect()
        time.sleep(0.2)

        self.assertFalse(host1.is_running())
        self.assertTrue(manager.is_running())

        data = manager.request_host_status(host1.config_file)
        self.assertFalse(data['started'])

        self.assertTrue(manager.is_running())

        host2.disconnect()
        time.sleep(0.2)

        self.assertFalse(host2.is_running())

        self.assertFalse(manager.is_running())