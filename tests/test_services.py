import os
import unittest
from service_host.manager import Manager
from service_host.service import Service
from .settings import PATH_TO_NODE, PATH_TO_NODE_MODULES


class TestServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_file = os.path.join(os.path.dirname(__file__), 'test_configs', 'test_services.services.config.js')
        cls.manager = Manager(
            path_to_node=PATH_TO_NODE,
            path_to_node_modules=PATH_TO_NODE_MODULES,
            config_file=config_file
        )
        cls.host = cls.manager.start_managed_host(config_file)

    def test_basic_service(self):
        class HelloWorld(Service):
            name = 'hello-world'
            host = self.host

        hello_world = HelloWorld()

        for i in range(5):
            res = hello_world.call(data={'name': 'world'})
            self.assertEqual(res.text, 'hello, world')