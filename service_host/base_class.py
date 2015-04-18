import json
import os
import subprocess
import requests
from requests.exceptions import ConnectionError
from .conf import settings, Verbosity


class BaseClass(object):
    path_to_node = None
    path_to_node_modules = None
    config_file = None
    type_name = None

    # Generated at runtime
    config = None
    is_connected = False

    def __init__(self, path_to_node, path_to_node_modules, config_file):
        self.path_to_node = path_to_node
        self.path_to_node_modules = path_to_node_modules
        self.config_file = config_file

        # Sanity checks
        assert self.path_to_node
        assert self.path_to_node_modules
        assert self.config_file
        assert self.type_name

        self.validate_config()
        self.connect()

    def get_path_to_bin(self):
        return os.path.join(self.path_to_node_modules, '.bin', 'service-host')

    def read_config_from_file(self):
        process = subprocess.Popen(
            (self.path_to_node, self.get_path_to_bin(), self.config_file, '--config',),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        process.wait()

        stderr = process.stderr.read()
        if stderr:
            raise Exception(stderr)

        output = process.stdout.read()

        return json.loads(output)

    def get_config(self):
        if not self.config:
            self.config = self.read_config_from_file()
        return self.config

    def validate_config(self):
        config = self.get_config()
        if 'address' not in config:
            raise Exception('No address has been defined in {config}'.format(config))
        if 'port' not in config:
            raise Exception('No address has been defined in {config}'.format(config))
        if 'services' not in config:
            raise Exception('No services have been defined in {config}'.format(config))

    def get_url(self, endpoint=None):
        config = self.get_config()
        return 'http://{address}:{port}/{endpoint}'.format(
            address=config['address'],
            port=config['port'],
            endpoint=endpoint or ''
        )

    def send_request(self, endpoint, params=None, post=None, data=None, content_type=None):
        url = self.get_url(endpoint)
        headers = None
        if content_type:
            headers = {'content-type': content_type}
        if post:
            return requests.post(url, data=data, params=params, headers=headers)
        return requests.get(url, params=params, headers=headers)

    def get_type_name(self):
        try:
            return self.send_request('type').text
        except ConnectionError:
            pass

    def is_running(self):
        return self.get_type_name() == self.type_name

    def request_config(self):
        res = self.send_request('config')

        if res.status_code != 200:
            raise Exception(
                'Unexpected response when requesting {type_name} config from {res_url}. {res_code}: {res_text}'.format(
                    type_name=self.type_name,
                    res_url=res.url,
                    res_code=res.status_code,
                    res_text=res.text,
                )
            )

        return res.json()

    def connect(self):
        if not self.is_running():
            raise Exception('Cannot connect to {}'.format(self.get_url()))

        config_subset = lambda config: {
            key: config[key] for key in config.keys() if key not in ('outputOnListen',)
        }

        expected_config = config_subset(self.get_config())
        actual_config = config_subset(self.request_config())

        if expected_config != actual_config:
            raise Exception(
                (
                    'The {type_name} at {url} is using a different config than expected. '
                    'Expected {expected}, received {actual}.'
                ).format(
                    type_name=self.type_name,
                    url=self.get_url(),
                    expected=expected_config,
                    actual=actual_config,
                )
            )

        if settings.VERBOSITY >= Verbosity.CONNECT:
            print('Connected to {type_name} at {url}'.format(
                type_name=self.type_name,
                url=self.get_url())
            )

        self.is_connected = True