import json
import requests
import unittest
import os
from requests.exceptions import ConnectionError as RequestsConnectionError
from js_host.js_host import JSHost
from js_host.base_server import BaseServer
from js_host.bin import read_status_from_config_file
from .utils import start_proxy, stop_proxy, start_host_process, stop_host_process
from .settings import ConfigFiles, JS_HOST


class TestJSHost(unittest.TestCase):
    process = None
    host = None

    @classmethod
    def setUpClass(cls):
        cls.host, cls.process = start_host_process(config_file=ConfigFiles.JS_HOST)
        cls.host.connect()

    @classmethod
    def tearDownClass(cls):
        stop_host_process(cls.host, cls.process)

    def test_inherits_from_base_server(self):
        self.assertIsInstance(self.host, BaseServer)

    def test_is_instantiated_properly(self):
        self.assertEqual(self.host.expected_type_name, 'Host')
        self.assertIsNotNone(self.host.status)
        self.assertIsInstance(self.host.status, dict)
        self.assertEqual(self.host.config_file, os.path.join(JS_HOST['SOURCE_ROOT'], JS_HOST['CONFIG_FILE']))

    def test_is_running(self):
        self.assertTrue(self.host.is_running())

    def test_can_read_in_config(self):
        self.assertEqual(self.host.get_config()['address'], '127.0.0.1')
        self.assertEqual(self.host.get_config()['port'], 30403)

    def test_can_produce_url_to_itself(self):
        self.assertEqual(self.host.get_url(), 'http://127.0.0.1:30403')
        self.assertEqual(self.host.get_url('some/endpoint'), 'http://127.0.0.1:30403/some/endpoint')

    def test_host_connection_lifecycle(self):
        host, process = start_host_process(port_override=0)

        self.assertNotEqual(host.get_config()['port'], 56789)

        self.assertFalse(host.has_connected)
        host.connect()
        self.assertTrue(host.has_connected)

        self.assertEqual(host.get_type_name(), 'Host')

        self.assertEqual(
            host.get_status(),
            host.request_status(),
        )

        res = host.send_request(
            'function/echo',
            data=json.dumps({'echo': 'foo'}),
            post=True,
            headers={'content-type': 'application/json'},
        )
        self.assertEqual(res.text, 'foo')

        stop_host_process(host, process)

        self.assertFalse(host.is_running())

        self.assertRaises(RequestsConnectionError, host.send_request, 'config')

    def test_proxied_host(self):
        self.assertRaises(RequestsConnectionError, requests.get, 'http://127.0.0.1:8000/status')

        proxy = start_proxy()

        data = requests.get('http://127.0.0.1:8000/status').json()

        self.assertEqual(data['config']['port'], 30403)

        proxied_host = JSHost(
            status=read_status_from_config_file(ConfigFiles.JS_HOST),
            config_file=ConfigFiles.JS_HOST,
        )
        proxied_host.root_url = 'http://127.0.0.1:8000'

        proxied_host.connect()

        self.assertEqual(proxied_host.get_status(), self.host.get_status())

        self.assertEqual(proxied_host.get_url('status'), 'http://127.0.0.1:8000/status')

        self.assertEqual(proxied_host.request_status(), self.host.request_status())

        count = self.host.send_json_request('function/counter').text
        proxied_count = proxied_host.send_json_request('function/counter').text
        self.assertEqual(int(proxied_count), int(count) + 1)

        self.host.send_json_request('function/counter')
        self.host.send_json_request('function/counter')

        proxied_count = proxied_host.send_json_request('function/counter').text
        self.assertEqual(int(proxied_count), int(count) + 4)

        stop_proxy(proxy)

        self.assertRaises(RequestsConnectionError, requests.get, 'http://127.0.0.1:8000/status')


