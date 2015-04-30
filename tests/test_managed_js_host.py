import json
import os
from js_host.exceptions import ConnectionError
from js_host.manager import JSHostManager
from js_host.js_host import JSHost
from .base_js_host_tests import BaseJSHostTests

managed_host_lifecycle_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'test_managed_js_host_lifecycle.host.config.js')


class TestManagedJSHost(BaseJSHostTests):
    __test__ = True
    manager = None

    @classmethod
    def setUpClass(cls):
        cls.manager = JSHostManager(config_file=cls.base_js_host_config_file)
        cls.manager.start()
        cls.manager.connect()
        
        cls.host = JSHost(manager=cls.manager)
        cls.host.start()
        cls.host.connect()

    @classmethod
    def tearDownClass(cls):
        cls.host.stop()
        cls.manager.stop()

    def test_can_read_in_config(self):
        self.assertEqual(self.host.get_config()['address'], '127.0.0.1')
        self.assertIsNotNone(self.host.get_config()['functions'])
        self.assertIsInstance(self.host.get_config(), dict)

        # Ensure the manager runs on the designated port and
        # the host runs on a different port
        self.assertEqual(self.host.manager.get_config()['port'], 56789)
        self.assertNotEqual(self.host.get_config()['port'], 56789)

    def test_can_produce_url_to_itself(self):
        self.assertNotEqual(self.host.get_config()['port'], 56789)
        # The host is running on a random port
        port = self.host.get_config()['port']
        self.assertEqual(self.host.get_url(), 'http://127.0.0.1:{}'.format(port))
        self.assertEqual(self.host.get_url('some/endpoint'), 'http://127.0.0.1:{}/some/endpoint'.format(port))

    def test_accepts_requests(self):
        res = self.host.send_request('status')
        self.assertEqual(
            json.loads(res.text),
            self.host.get_status()
        )

    def test_managed_host_lifecycle(self):
        manager = JSHostManager(config_file=managed_host_lifecycle_config_file)

        self.assertEqual(manager.get_config()['port'], 23456)

        manager.start()
        manager.connect()

        self.assertTrue(manager.is_running())

        host = JSHost(manager=manager)

        # Should not be able to connect, even though a manager is running
        # on the expected port
        self.assertEqual(host.get_config()['port'], 23456)
        self.assertRaises(ConnectionError, host.connect)
        self.assertFalse(host.is_running())

        host.start()
        self.assertTrue(host.is_running())

        host.connect()
        self.assertTrue(host.is_running())

        host.stop()
        self.assertFalse(host.is_running())
        self.assertRaises(ConnectionError, host.connect)

        manager.stop()

    def test_can_restart(self):
        port = self.host.get_config()['port']
        self.host.restart()
        self.assertTrue(self.host.is_running())
        self.assertNotEqual(port, self.host.get_config()['port'])