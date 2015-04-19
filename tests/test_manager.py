# import os
# import unittest
# import subprocess
# import json
# import atexit
# from service_host.base_server import BaseServer
# from service_host.exceptions import ServiceError, ConnectionError, ServiceTimeout
# from service_host.manager import ServiceHost
# from service_host.conf import settings, Verbosity
# from .settings import PATH_TO_NODE, PATH_TO_NODE_MODULES
#
# service_host_config_file = os.path.join(os.path.dirname(__file__), 'test_configs', 'test_service_host.services.config.js')
#
# # Some config values tend to mutate based on the params used to invoke a host,
# # so we can't rely on them to match those read in during a host's init
# blacklisted_config_keys = ('outputOnListen',)
#
#
# def subset_config(config):
#     return {
#         key: config[key] for key in config if key not in blacklisted_config_keys
#     }
#
#
# def start_host_process(host, port_override=None):
#     assert isinstance(host, ServiceHost)
#
#     cmd = (
#         host.path_to_node,
#         host.get_path_to_bin(),
#         host.config_file,
#         '--json'
#     )
#
#     if port_override is not None:
#         cmd += ('--port', str(port_override))
#
#     process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#
#     output = process.stdout.readline()
#
#     if not output.startswith('{'):
#         raise Exception('Unexpected output from `{}`: {}'.format(' '.join(cmd), output))
#
#     config = json.loads(output)
#
#     if port_override is not None:
#         if port_override != 0:
#             assert config['port'] == port_override
#         host.config['port'] = config['port']
#
#     if subset_config(config) != subset_config(host.config):
#         raise Exception(
#             'Unexpected output {}. Expected {}'.format(subset_config(host.config), subset_config(config))
#         )
#
#     if settings.VERBOSITY == Verbosity.ALL:
#         print('Started {}'.format(host.get_name()))
#
#     atexit.register(stop_host_process, host=host, process=process)
#
#     return process
#
#
# def stop_host_process(host, process):
#     # Sanity checks
#     assert isinstance(host, ServiceHost)
#     assert process is not None
#
#     if host.is_running():
#         process.kill()
#         if settings.VERBOSITY == Verbosity.ALL:
#             print('Stopped {}'.format(host.get_name()))
#
#
# class TestBaseServer(unittest.TestCase):
#     host = ServiceHost(
#         path_to_node=PATH_TO_NODE,
#         path_to_node_modules=PATH_TO_NODE_MODULES,
#         config_file=service_host_config_file
#     )
#
#     process = None
#
#     @classmethod
#     def setUpClass(cls):
#         cls.process = start_host_process(cls.host)
#         cls.host.connect()
#
#     @classmethod
#     def tearDownClass(cls):
#         stop_host_process(cls.host, cls.process)
#
#     def test_inherits_from_base_server(self):
#         self.assertIsInstance(self.host, BaseServer)
#
#     def test_is_instantiated_properly(self):
#         self.assertEqual(self.host.type_name, 'Host')
#         self.assertEqual(self.host.config_file, service_host_config_file)
#         self.assertEqual(self.host.path_to_node, PATH_TO_NODE)
#         self.assertEqual(self.host.path_to_node_modules, PATH_TO_NODE_MODULES)
#         self.assertIsNotNone(self.host.config)
#         self.assertIsInstance(self.host.config, dict)
#
#     def test_can_read_in_config(self):
#         self.assertEqual(self.host.get_config(), self.host.config)
#         self.assertEqual(self.host.config['address'], '127.0.0.1')
#         self.assertEqual(self.host.config['port'], 56789)
#
#     def test_can_produce_url_to_itself(self):
#         self.assertEqual(self.host.get_url(), 'http://127.0.0.1:56789')
#         self.assertEqual(self.host.get_url('some/endpoint'), 'http://127.0.0.1:56789/some/endpoint')
#
#     def test_is_running(self):
#         self.assertTrue(self.host.is_running())
#
#     def test_host_connection_lifecycle(self):
#         host = ServiceHost(
#             path_to_node=PATH_TO_NODE,
#             path_to_node_modules=PATH_TO_NODE_MODULES,
#             config_file=service_host_config_file,
#         )
#
#         process = start_host_process(host, port_override=0)
#
#         self.assertFalse(host.has_connected)
#         host.connect()
#         self.assertTrue(host.has_connected)
#
#         self.assertEqual(host.request_type_name(), 'Host')
#
#         self.assertEqual(
#             subset_config(host.request_config()),
#             subset_config(host.config)
#         )
#
#         self.assertEqual(
#             subset_config(host.request_config()),
#             subset_config(host.config)
#         )
#
#         res = host.send_request_to_service('echo', data=json.dumps({'echo': 'foo'}))
#         self.assertEqual(res.text, 'foo')
#
#         stop_host_process(host, process)
#
#         self.assertFalse(host.is_running())
#
#         self.assertRaises(ConnectionError, host.send_request_to_service, 'error')
#
#     def test_can_handle_errors(self):
#         self.assertRaises(ServiceError, self.host.send_request_to_service, 'echo')
#
#         self.assertRaises(ServiceError, self.host.send_request_to_service, 'async-echo')
#
#         self.assertRaises(ServiceError, self.host.send_request_to_service, 'error')
#
#         try:
#             self.host.send_request_to_service('error')
#             raise Exception('A ServiceError should have been raised before this line')
#         except ServiceError, e:
#             self.assertIn('Hello from error service', e.message)
#
#     def test_can_cache_content(self):
#         res = self.host.send_request_to_service('echo', data=json.dumps({'echo': 'test1'}), cache_key='foo')
#         self.assertEqual(res.text, 'test1')
#
#         res = self.host.send_request_to_service('echo', data=json.dumps({'echo': 'test2'}), cache_key='bar')
#         self.assertEqual(res.text, 'test2')
#
#         res = self.host.send_request_to_service('echo', data=json.dumps({'echo': 'test3'}), cache_key='foo')
#         self.assertEqual(res.text, 'test1')
#
#         res = self.host.send_request_to_service('echo-data', data=json.dumps({'echo': 'test4'}), cache_key='foo')
#         self.assertEqual(json.loads(res.text), {'echo': 'test4'})
#
#         res = self.host.send_request_to_service('echo-data', data=json.dumps({'echo': 'test5'}), cache_key='bar')
#         self.assertEqual(json.loads(res.text), {'echo': 'test5'})
#
#         res = self.host.send_request_to_service('echo-data', data=json.dumps({'echo': 'test6'}), cache_key='foo')
#         self.assertEqual(json.loads(res.text), {'echo': 'test4'})
#
#         res = self.host.send_request_to_service('async-echo', data=json.dumps({'echo': 'test7'}), cache_key='foo')
#         self.assertEqual(res.text, 'test7')
#
#         res = self.host.send_request_to_service('async-echo', data=json.dumps({'echo': 'test8'}), cache_key='bar')
#         self.assertEqual(res.text, 'test8')
#
#         res = self.host.send_request_to_service('async-echo', data=json.dumps({'echo': 'test9'}), cache_key='foo')
#         self.assertEqual(res.text, 'test7')
#
#     def test_can_handle_service_timeouts(self):
#         self.assertRaises(
#             ServiceTimeout,
#             self.host.send_request_to_service,
#             'async-echo',
#             timeout=0.2
#         )
#
#         res = self.host.send_request_to_service('echo', data=json.dumps({'echo': 'bar'}), timeout=0.2)
#         self.assertEqual(res.text, 'bar')
#
#     def test_raises_on_start_or_stop_calls(self):
#         self.assertRaises(NotImplementedError, self.host.start)
#         self.assertRaises(NotImplementedError, self.host.stop)