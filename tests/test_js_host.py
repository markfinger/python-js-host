import json
from js_host.exceptions import ConnectionError
from js_host.js_host import JSHost
from .common_js_host_tests import CommonJSHostTests
from .utils import start_host_process, stop_host_process


class TestJSHost(CommonJSHostTests):
    __test__ = True
    process = None

    @classmethod
    def setUpClass(cls):
        cls.host = JSHost(config_file=cls.common_js_host_config_file)
        cls.process = start_host_process(cls.host)
        cls.host.connect()

    @classmethod
    def tearDownClass(cls):
        stop_host_process(cls.host, cls.process)

    def test_can_read_in_config(self):
        self.assertEqual(self.host.get_config(), self.host.config)
        self.assertEqual(self.host.config['address'], '127.0.0.1')
        self.assertEqual(self.host.config['port'], 56789)

    def test_can_produce_url_to_itself(self):
        self.assertEqual(self.host.get_url(), 'http://127.0.0.1:56789')
        self.assertEqual(self.host.get_url('some/endpoint'), 'http://127.0.0.1:56789/some/endpoint')

    def test_host_connection_lifecycle(self):
        host = JSHost(config_file=self.common_js_host_config_file)

        self.assertEqual(host.config['port'], 56789)
        process = start_host_process(host, port_override=0)
        self.assertNotEqual(host.config['port'], 56789)

        self.assertFalse(host.has_connected)
        host.connect()
        self.assertTrue(host.has_connected)

        self.assertEqual(host.request_type_name(), 'Host')

        self.assertEqual(
            host.get_comparable_config(host.request_config()),
            host.get_comparable_config(host.config)
        )

        res = host.call_function('echo', data=json.dumps({'echo': 'foo'}))
        self.assertEqual(res.text, 'foo')

        stop_host_process(host, process)

        self.assertFalse(host.is_running())

        self.assertRaises(ConnectionError, host.call_function, 'error')
        
    def test_raises_on_start_or_stop_calls(self):
        self.assertRaises(NotImplementedError, self.host.start)
        self.assertRaises(NotImplementedError, self.host.stop)