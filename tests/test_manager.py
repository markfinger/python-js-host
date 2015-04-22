import json
import os
import unittest
from service_host.base_server import BaseServer
from service_host.exceptions import ConnectionError
from service_host.manager import Manager
from service_host.managed_service_host import ManagedServiceHost
from service_host.conf import settings

manager_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'test_manager.services.config.js')
manager_lifecycle_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'test_manager_lifecycle.services.config.js')


class TestManager(unittest.TestCase):
    manager = None

    @classmethod
    def setUpClass(cls):
        cls.manager = Manager(
            path_to_node=settings.PATH_TO_NODE,
            source_root=settings.SOURCE_ROOT,
            config_file=manager_config_file
        )
        cls.manager.start()
        cls.manager.connect()

    @classmethod
    def tearDownClass(cls):
        cls.manager.stop()

    def test_inherits_from_base_server(self):
        self.assertIsInstance(self.manager, BaseServer)

    def test_is_instantiated_properly(self):
        self.assertEqual(self.manager.type_name, 'Manager')
        self.assertEqual(self.manager.config_file, manager_config_file)
        self.assertEqual(self.manager.path_to_node, settings.PATH_TO_NODE)
        self.assertEqual(self.manager.source_root, settings.SOURCE_ROOT)
        self.assertIsNotNone(self.manager.config)
        self.assertIsInstance(self.manager.config, dict)

    def test_can_read_in_config(self):
        self.assertEqual(self.manager.get_config(), self.manager.config)
        self.assertEqual(self.manager.config['address'], '127.0.0.1')
        self.assertEqual(self.manager.config['port'], 45678)
        self.assertIsNone(self.manager.config['services'])

    def test_can_produce_url_to_itself(self):
        self.assertEqual(self.manager.get_url(), 'http://127.0.0.1:45678')
        self.assertEqual(self.manager.get_url('some/endpoint'), 'http://127.0.0.1:45678/some/endpoint')

    def test_is_running(self):
        self.assertTrue(self.manager.is_running())

    def test_accepts_requests(self):
        res = self.manager.send_request('config')
        self.assertEqual(
            self.manager.get_comparable_config(json.loads(res.text)),
            self.manager.get_comparable_config(self.manager.config)
        )

    def test_manager_lifecycle(self):
        manager = Manager(
            path_to_node=settings.PATH_TO_NODE,
            source_root=settings.SOURCE_ROOT,
            config_file=manager_lifecycle_config_file,
        )

        self.assertEqual(manager.config['port'], 34567)

        self.assertRaises(ConnectionError, manager.connect)

        self.assertFalse(manager.is_running())

        self.assertRaises(ConnectionError, manager.connect)

        manager.start()

        manager.connect()

        self.assertTrue(manager.is_running())

        manager.stop()

        self.assertFalse(manager.is_running())

        self.assertRaises(ConnectionError, manager.connect)

    def test_managers_stop_once_the_last_host_has(self):
        manager = Manager(
            path_to_node=settings.PATH_TO_NODE,
            source_root=settings.SOURCE_ROOT,
            config_file=manager_lifecycle_config_file,
        )

        manager.start()
        manager.connect()

        host1 = ManagedServiceHost(manager)
        host1.start()
        host1.connect()

        self.assertTrue(host1.is_running())

        host2 = ManagedServiceHost(manager, config_file=manager_config_file)
        host2.start()
        host2.connect()

        self.assertNotEqual(host1.config['port'], host2.config['port'])

        self.assertTrue(host2.is_running())

        host1.stop()

        self.assertTrue(manager.is_running())

        host2.stop()

        self.assertFalse(manager.is_running())