import json
import requests
import warnings
from requests.exceptions import ConnectionError as RequestsConnectionError
from .conf import settings
from .utils import six, verbosity
from .exceptions import ConfigError, ConnectionError, UnexpectedResponse


class BaseServer(object):
    supported_version = ('0', '11')
    status = None
    config_file = None
    root_url = None

    # Defined by subclasses
    expected_type_name = None

    has_connected = False

    def __init__(self, status, config_file=None, root_url=None):
        self.status = status

        if config_file is not None:
            self.config_file = config_file

        if root_url is not None:
            self.root_url = settings.get_root_url()

        self.validate_status()

    def get_name(self):
        url = self.root_url

        if not url:
            config = self.get_config()
            url = '{}:{}'.format(config['address'], config['port'])

        return '{} [{}]'.format(type(self).__name__, url)

    def get_status(self):
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

    def validate_status(self):
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

    def connect(self):
        if not self.is_running():
            raise ConnectionError('Cannot connect to {}'.format(self.get_name()))

        local = self.get_status()
        remote = self.request_status()

        if remote != local:
            raise UnexpectedResponse(
                (
                    'Cannot complete connection due to differences in local status and remote status. '
                    'Local: {local}. Remote: {remote}.'
                ).format(
                    local=local,
                    remote=remote,
                )
            )

        if settings.VERBOSITY >= verbosity.CONNECT:
            print('Connected to {}'.format(self.get_name()))

        self.has_connected = True