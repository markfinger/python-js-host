import sys
import json
import os
import subprocess
import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from optional_django import six
from .conf import settings, Verbosity
from .exceptions import ConfigError, ConnectionError, UnexpectedResponse


class BaseServer(object):
    # Config
    path_to_node = None
    path_to_node_modules = None
    config_file = None

    # Defined by subclasses
    type_name = None

    # Generated at runtime
    config = None
    has_connected = False

    # When connecting to hosts, we read their config in and ensure that it matches
    # what we are expected. In some instances, certain config values will be mutated
    # based on the params used to invoke a host, so we need to omit them when
    # comparing configs
    _ignorable_config_keys = ('outputOnListen',)

    def __init__(self, path_to_node, path_to_node_modules, config_file):
        self.path_to_node = path_to_node
        self.path_to_node_modules = path_to_node_modules
        self.config_file = config_file

        # Sanity checks
        assert self.path_to_node
        assert self.path_to_node_modules
        assert self.config_file
        assert self.type_name

        self.validate_config(self.get_config())

    def get_name(self):
        config = self.get_config()
        return '{} [{}]'.format(
            type(self).__name__,
            '{}:{}'.format(config['address'], config['port'])
        )

    def get_path_to_bin(self):
        return os.path.join(self.path_to_node_modules, '.bin', 'service-host')

    def read_config_from_file(self):
        if settings.VERBOSITY >= Verbosity.ALL:
            print('Reading config file {}'.format(self.config_file))

        try:
            output = subprocess.check_output(
                (self.path_to_node, self.get_path_to_bin(), self.config_file, '--config',),
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError, e:
            raise six.reraise(ConfigError, ConfigError(*e.args), sys.exc_info()[2])

        return json.loads(output)

    def get_config(self):
        if not self.config:
            self.config = self.read_config_from_file()
        return self.config

    def validate_config(self, config):
        if config is None:
            raise ConfigError('No config has been defined')
        if 'address' not in config:
            raise ConfigError('No address has been defined in {}'.format(config))
        if 'port' not in config:
            raise ConfigError('No port has been defined in {}'.format(config))

    def get_url(self, endpoint=None):
        config = self.get_config()
        return 'http://{address}:{port}{sep}{endpoint}'.format(
            address=config['address'],
            port=config['port'],
            sep='/' if endpoint else '',
            endpoint=endpoint or '',
        )

    def send_request(self, endpoint, post=None, params=None, headers=None, data=None, timeout=None, unsafe=None):
        if not unsafe and not self.has_connected:
            raise ConnectionError(
                '{name} has not opened a connection yet. Call `connect()`'.format(name=self.get_name())
            )

        url = self.get_url(endpoint)

        if post:
            return requests.post(url, params=params, headers=headers, data=data, timeout=timeout)

        return requests.get(url, params=params, headers=headers, timeout=timeout)

    def request_type_name(self):
        try:
            return self.send_request('type', unsafe=True).text
        except RequestsConnectionError:
            pass

    def request_config(self):
        try:
            res = self.send_request('config', unsafe=True)
        except RequestsConnectionError:
            raise ConnectionError('Cannot read config from {}'.format(self.get_name()))

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Expected config from {name}. Received {res_code}: {res_text}'.format(
                    self.get_name(),
                    res_code=res.status_code,
                    res_text=res.text,
                )
            )

        return res.json()

    def is_running(self):
        return self.request_type_name() == self.type_name

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def get_comparable_config(self, config):
        return {
            key: config[key] for key in config.keys() if key not in self._ignorable_config_keys
        }

    def connect(self):
        if not self.is_running():
            raise ConnectionError('Cannot connect to {}'.format(self.get_name()))

        expected_config = self.get_comparable_config(self.get_config())
        actual_config = self.get_comparable_config(self.request_config())

        if expected_config != actual_config:
            raise ConfigError(
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

        self.has_connected = True