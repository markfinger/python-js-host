import json
import os
import subprocess
import requests
import warnings
from optional_django import six
from distutils.spawn import find_executable
from requests.exceptions import ConnectionError as RequestsConnectionError
from .conf import settings
from .verbosity import VERBOSE, CONNECT
from .exceptions import ConfigError, ConnectionError, UnexpectedResponse


class BaseServer(object):
    supported_version = ('0', '11')

    # Config
    path_to_node = None
    source_root = None
    config_file = None
    root_url = settings.ROOT_URL

    # Defined by subclasses
    expected_type_name = None
    read_config_file_params = ()

    # Generated at runtime
    status = None

    config = None
    version = None
    has_connected = False

    def __init__(self, config_file=None, source_root=None, path_to_node=None):
        if not self.config_file:
            self.config_file = config_file or settings.CONFIG_FILE
        if not self.source_root:
            self.source_root = source_root or settings.SOURCE_ROOT
        if not self.path_to_node:
            self.path_to_node = path_to_node or settings.PATH_TO_NODE

        for setting in ('config_file', 'source_root', 'path_to_node'):
            if not getattr(self, setting):
                raise ConfigError(
                    (
                        'A default value for {name}.{setting} has not been defined. Please define defaults '
                        'in js_host.conf.settings'
                    ).format(
                        name=type(self).__name__,
                        setting=setting,
                    )
                )

        if not find_executable(self.path_to_node):
            raise ConfigError(
                (
                    'Executable "{}" does not exist. Please define the PATH_TO_NODE setting in '
                    'js_host.conf.settings'
                ).format(self.path_to_node)
            )

        if not os.path.exists(self.source_root) or not os.path.isdir(self.source_root):
            raise ConfigError('Source root {} does not exist or is not a directory'.format(self.source_root))

        if not os.path.exists(self.get_path_to_config_file()):
            raise ConfigError('Config file {} does not exist'.format(self.get_path_to_config_file()))

        version = self.get_version().split('.')
        for i, number in enumerate(self.supported_version):
            if version[i] != number:
                raise ConfigError(
                    'Version {} of the js-host JavaScript library is supported, the system reported {}'.format(
                        '.'.join(self.supported_version),
                        self.get_version(),
                    )
                )

        type_name = self.get_type_name()
        if type_name != self.expected_type_name:
            raise ConfigError('Expected type {} but found {}'.format(self.expected_type_name, type_name))

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
        address = self.root_url

        if not address:
            config = self.get_config()
            address = '{}:{}'.format(config['address'], config['port'])

        return '{} [{}]'.format(type(self).__name__, address)

    def get_path_to_bin(self):
        if os.path.isabs(settings.BIN_PATH):
            return settings.BIN_PATH
        return os.path.join(self.source_root, settings.BIN_PATH)

    def read_config_file(self, config_file):
        if settings.VERBOSITY >= VERBOSE:
            print('Reading config file {}'.format(config_file))

        process = subprocess.Popen(
            (self.path_to_node, self.get_path_to_bin(), config_file, '--config',) + self.read_config_file_params,
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

    def get_status(self):
        if not self.status:
            self.status = self.read_config_file(self.get_path_to_config_file())
        return self.status

    def get_version(self):
        return self.get_status()['version']

    def get_type_name(self):
        return self.get_status()['type']

    def get_config(self):
        return self.get_status()['config']

    def get_url(self, endpoint=None):
        url = self.root_url

        if not url:
            config = self.get_config()
            url = 'http://{address}:{port}'.format(
                address=config['address'],
                port=config['port'],
            )

        return '{url}{sep}{endpoint}'.format(
            url=url,
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

    def send_json_request(self, *args, **kwargs):
        kwargs['post'] = True
        kwargs['headers'] = {'content-type': 'application/json'}

        if 'data' in kwargs and not isinstance(kwargs['data'], six.string_types):
            kwargs['data'] = json.dumps(kwargs['data'])

        return self.send_request(*args, **kwargs)

    def request_status(self):
        try:
            res = self.send_request('status', unsafe=True)
        except RequestsConnectionError:
            return

        try:
            return res.json()
        except ValueError:
            return None

    def is_running(self):
        expected_status = self.get_status()
        actual_status = self.request_status()

        if not actual_status:
            return False

        if expected_status == actual_status:
            return True

        if 'version' in actual_status and 'version' in expected_status:
            expected_version = expected_status['version']
            actual_version = actual_status['version']
            if expected_version != actual_version:
                warnings.warn(
                    (
                        'Remote js-host server appears to be using a different version. Expected {} but found {}. '
                        'Connections will not be opened unless the versions match'
                    ).format(expected_version, actual_version)
                )

        return False

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def restart(self):
        raise NotImplementedError()

    def connect(self):
        if not self.is_running():
            raise ConnectionError('Cannot connect to {}'.format(self.get_name()))

        expected = self.get_status()
        actual = self.request_status()

        if actual != expected:
            raise UnexpectedResponse(
                'Cannot complete connection. Expected {expected}, received {actual}.'.format(
                    expected=expected,
                    actual=actual,
                )
            )

        if settings.VERBOSITY >= CONNECT:
            print('Connected to {}'.format(self.get_name()))

        self.has_connected = True