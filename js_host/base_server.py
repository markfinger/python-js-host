import json
import os
import subprocess
import requests
from distutils.spawn import find_executable
from requests.exceptions import ConnectionError as RequestsConnectionError
from .conf import settings, Verbosity
from .exceptions import ConfigError, ConnectionError, UnexpectedResponse


class BaseServer(object):
    # Config
    path_to_node = None
    source_root = None
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

    def __init__(self, config_file=None, source_root=None, path_to_node=None):
        self.config_file = config_file or settings.CONFIG_FILE
        self.source_root = source_root or settings.SOURCE_ROOT
        self.path_to_node = path_to_node or settings.PATH_TO_NODE

        for setting in ('config_file', 'source_root', 'path_to_node'):
            if not getattr(self, setting):
                raise ConfigError(
                    (
                        '{name}.{setting} has not been defined. Define defaults by calling '
                        'js_host.conf.settings.configure({setting_upper}=VALUE)'
                    ).format(
                        name=type(self).__name__,
                        setting=setting,
                        setting_upper=setting.upper(),
                    )
                )

        if not find_executable(self.path_to_node):
            raise ConfigError(
                (
                    'Executable "{}" does not exist. To define a path to a node binary, call '
                    'js_host.conf.settings.configure(PATH_TO_NODE=\'/abs/path/to/node\')'
                ).format(self.path_to_node)
            )

        if not os.path.exists(self.source_root) or not os.path.isdir(self.source_root):
            raise ConfigError('Source root {} does not exist or is not a directory'.format(self.source_root))

        if not os.path.exists(self.get_path_to_config_file()):
            raise ConfigError('Config file {} does not exist'.format(self.get_path_to_config_file()))

        # Validate the config file
        config = self.get_config()
        if config is None:
            raise ConfigError('No config has been defined')
        if 'address' not in config:
            raise ConfigError('No address has been defined in {}'.format(config))
        if 'port' not in config:
            raise ConfigError('No port has been defined in {}'.format(config))

    def get_path_to_config_file(self):
        if os.path.isabs(self.config_file):
            return self.config_file
        return os.path.join(self.source_root, self.config_file)

    def get_name(self):
        config = self.get_config()
        return '{} [{}]'.format(
            type(self).__name__,
            '{}:{}'.format(config['address'], config['port'])
        )

    def get_path_to_bin(self):
        if os.path.isabs(settings.BIN_PATH):
            return settings.BIN_PATH
        return os.path.join(self.source_root, settings.BIN_PATH)

    def read_config_from_file(self, config_file):
        if settings.VERBOSITY >= Verbosity.ALL:
            print('Reading config file {}'.format(config_file))

        process = subprocess.Popen(
            (self.path_to_node, self.get_path_to_bin(), config_file, '--config',),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        process.wait()

        stderr = process.stderr.read()
        if stderr:
            raise ConfigError(stderr)

        stdout = process.stdout.read()
        stdout = stdout.decode('utf-8')

        return json.loads(stdout)

    def get_config(self):
        if not self.config:
            self.config = self.read_config_from_file(self.get_path_to_config_file())
        return self.config

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

        func = requests.post if post else requests.get

        kwargs = {
            'params': params,
            'headers': headers,
            'timeout': timeout
        }
        if post:
            kwargs['data'] = data

        return func(url, **kwargs)

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
                'Expected {name} to return its config. Received {res_code}: {res_text}'.format(
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
            print('Connected to {}'.format(self.get_name()))

        self.has_connected = True