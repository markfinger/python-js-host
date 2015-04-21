import json
from service_host.exceptions import ConnectionError
from service_host.service_host import ServiceHost
from service_host.conf import settings
from .common_service_host_tests import CommonServiceHostTests
from .utils import start_host_process, stop_host_process


class TestServiceHost(CommonServiceHostTests):
    __test__ = True
    process = None

    @classmethod
    def setUpClass(cls):
        cls.host = ServiceHost(
            path_to_node=settings.PATH_TO_NODE,
            path_to_node_modules=settings.PATH_TO_NODE_MODULES,
            config_file=cls.common_service_host_config_file
        )
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
        host = ServiceHost(
            path_to_node=settings.PATH_TO_NODE,
            path_to_node_modules=settings.PATH_TO_NODE_MODULES,
            config_file=self.common_service_host_config_file,
        )

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

        res = host.send_request_to_service('echo', data=json.dumps({'echo': 'foo'}))
        self.assertEqual(res.text, 'foo')

        stop_host_process(host, process)

        self.assertFalse(host.is_running())

        self.assertRaises(ConnectionError, host.send_request_to_service, 'error')
        
    def test_raises_on_start_or_stop_calls(self):
        self.assertRaises(NotImplementedError, self.host.start)
        self.assertRaises(NotImplementedError, self.host.stop)