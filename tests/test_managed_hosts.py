import os
import unittest
from service_host.manager import Manager
from .settings import PATH_TO_NODE, PATH_TO_NODE_MODULES


class TestServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config_file = os.path.join(
            os.path.dirname(__file__), 'test_configs', 'test_managed_hosts.services.config.js'
        )
        cls.manager = Manager(
            path_to_node=PATH_TO_NODE,
            path_to_node_modules=PATH_TO_NODE_MODULES,
            config_file=cls.config_file
        )

    def test_managed_host_restart(self):
        host = self.manager.start_managed_host(self.config_file)
        port = host.config['port']
        host.restart()
        self.assertNotEqual(port, host.config['port'])