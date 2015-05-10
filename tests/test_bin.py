import os
import unittest
import json
from js_host.bin import read_status_from_config_file
from .settings import TEST_ROOT, ConfigFiles


class TestBin(unittest.TestCase):
    def test_can_read_status_from_a_config_file(self):
        status = read_status_from_config_file(ConfigFiles.BASE_SERVER)
        self.assertEqual(status['type'], 'Host')
        self.assertIsInstance(status['config'], dict)

        with open(os.path.join(TEST_ROOT, 'node_modules', 'js-host', 'package.json'), 'r') as package:
            self.assertEqual(status['version'], json.loads(package.read())['version'])

        self.assertEqual(status['config']['address'], '127.0.0.1')
        self.assertEqual(status['config']['port'], 9876)
        self.assertEqual(status['config']['someUnexpectedProp'], 'foo')
