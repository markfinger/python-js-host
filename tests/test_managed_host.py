import json
import os
from service_host.exceptions import ConnectionError
from service_host.manager import Manager
from service_host.managed_service_host import ManagedServiceHost
from .common_service_host_tests import CommonServiceHostTests

managed_host_lifecycle_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'test_managed_host_lifecycle.services.config.js')


class TestManagedHost(CommonServiceHostTests):
    __test__ = True
    manager = None

    @classmethod
    def setUpClass(cls):
        cls.manager = Manager(config_file=cls.common_service_host_config_file)
        cls.manager.start()
        cls.manager.connect()
        
        cls.host = ManagedServiceHost(cls.manager)
        cls.host.start()
        cls.host.connect()

    @classmethod
    def tearDownClass(cls):
        cls.host.stop()
        cls.manager.stop()

    def test_can_read_in_config(self):
        self.assertEqual(self.host.get_config(), self.host.config)
        self.assertEqual(self.host.config['address'], '127.0.0.1')
        self.assertIsNotNone(self.host.config['services'])
        self.assertIsInstance(self.host.config, dict)

        # Ensure the manager runs on the designated port and
        # the host runs on a different port
        self.assertEqual(self.manager.config['port'], 56789)
        self.assertNotEqual(self.host.config['port'], 56789)

    def test_can_produce_url_to_itself(self):
        self.assertNotEqual(self.host.config['port'], 56789)
        # The host is running on a random port
        port = self.host.config['port']
        self.assertEqual(self.host.get_url(), 'http://127.0.0.1:{}'.format(port))
        self.assertEqual(self.host.get_url('some/endpoint'), 'http://127.0.0.1:{}/some/endpoint'.format(port))

    def test_accepts_requests(self):
        res = self.host.send_request('config')
        self.assertEqual(
            self.host.get_comparable_config(json.loads(res.text)),
            self.host.get_comparable_config(self.host.config)
        )

    def test_managed_host_lifecycle(self):
        manager = Manager(config_file=managed_host_lifecycle_config_file)

        self.assertEqual(manager.config['port'], 23456)

        manager.start()
        manager.connect()

        self.assertTrue(manager.is_running())

        host = ManagedServiceHost(manager)

        # Should not be able to connect, even though a manager is running
        # on the expected port
        self.assertEqual(host.config['port'], 23456)
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