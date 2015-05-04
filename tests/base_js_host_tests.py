import os
from js_host.base_server import BaseServer
from js_host.conf import settings


class BaseJSHostTests(object):
    """
    A common test suite to be run over a JSHost of various configurations
    """
    # Subclasses should set this to True, to ensure the test runner
    # starts those tests
    __test__ = False

    host = None
    base_js_host_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'base_js_host_tests.host.config.js')

    def test_inherits_from_base_server(self):
        self.assertIsInstance(self.host, BaseServer)

    def test_is_instantiated_properly(self):
        self.assertEqual(self.host.expected_type_name, 'Host')
        self.assertEqual(self.host.path_to_node, settings.PATH_TO_NODE)
        self.assertEqual(self.host.source_root, settings.SOURCE_ROOT)
        self.assertIsNotNone(self.host.status)
        self.assertIsInstance(self.host.status, dict)
        self.assertEqual(self.host.config_file, self.base_js_host_config_file)

    def test_is_running(self):
        self.assertTrue(self.host.is_running())