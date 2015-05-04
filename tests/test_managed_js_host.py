import json
import os
import unittest
from optional_django import six
from js_host.exceptions import UnexpectedResponse, ProcessError
from js_host.manager import JSHostManager
from js_host.js_host import JSHost
from .base_js_host_tests import BaseJSHostTests

managed_host_lifecycle_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'test_managed_js_host_lifecycle.host.config.js')


class TestManagedJSHost(unittest.TestCase, BaseJSHostTests):
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

        host1 = JSHost(manager=manager)

        # Should not be able to connect, even though a manager is running
        # on the expected port
        self.assertEqual(host1.get_config()['port'], 23456)
        self.assertRaises(UnexpectedResponse, host1.connect)
        self.assertFalse(host1.is_running())

        host1.start()
        self.assertTrue(host1.is_running())

        host1.connect()
        self.assertTrue(host1.is_running())

        res = host1.send_json_request('function/test')
        self.assertEqual(res.text, 'test')

        host1.disconnect()
        self.assertTrue(host1.is_running())

        host2 = JSHost(manager=manager)

        host2.connect()

        self.assertIsInstance(host2.logfile, six.string_types)
        self.assertEqual(host2.logfile, host1.logfile)

        res = host2.send_json_request('function/test')
        self.assertEqual(res.text, 'test')

        host2.disconnect()
        self.assertTrue(host1.is_running())

        host2.stop()
        self.assertFalse(host2.is_running())
        self.assertRaises(UnexpectedResponse, host2.connect)

        manager.stop()

    def test_can_restart(self):
        count1 = int(self.host.send_json_request('function/counter').text)
        count2 = int(self.host.send_json_request('function/counter').text)
        self.assertEqual(count2, count1 + 1)

        port = self.host.get_config()['port']
        logfile = self.host.logfile

        self.host.restart()
        self.assertTrue(self.host.is_running())
        self.assertEqual(int(self.host.send_json_request('function/counter').text), 1)
        self.assertEqual(int(self.host.send_json_request('function/counter').text), 2)

        # Ensure the host continues to run on the same port
        self.assertEqual(port, self.host.get_config()['port'])

        # Ensure the same logfile is used
        host_status = self.manager.request_host_status(self.host.get_path_to_config_file())
        self.assertEqual(host_status['host']['logfile'], logfile)
        self.assertEqual(logfile, self.host.logfile)

    def test_its_output_is_written_to_a_logfile(self):
        self.assertIsInstance(self.host.logfile, six.string_types)
        with open(self.host.logfile, 'r') as logfile:
            logfile.read()
            self.host.send_request('status')
            new_content = logfile.read()
            self.assertIn('GET /status', new_content)
            res = self.host.send_request('function/error', post=True, headers={'content-type': 'application/json'})
            self.assertEqual(res.status_code, 500)
            error_content = logfile.read()
            self.assertIn('Hello from error function', error_content)

    def test_if_a_managed_host_crashes_the_exception_points_to_the_logfile(self):
        manager = JSHostManager(config_file=managed_host_lifecycle_config_file)
        manager.start()
        manager.connect()

        host = JSHost(manager=manager)
        host.start()
        host.connect()

        self.assertEqual(host.send_json_request('function/test').text, 'test')

        self.assertIsNotNone(host.logfile)

        host.stop()

        try:
            host.send_json_request('function/test')
        except ProcessError as e:
            self.assertIn(
                '{} appears to have crashed, you can inspect the log file at {}'.format(
                    host.get_name(),
                    host.logfile,
                ),
                str(e),
            )

        manager.stop()