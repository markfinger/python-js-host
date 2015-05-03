import hashlib
import json
import sys
from optional_django import six
from optional_django.serializers import JSONEncoder
from requests.exceptions import ConnectionError as RequestsConnectionError, ReadTimeout
from .conf import settings
from .verbosity import FUNCTION_CALL
from .exceptions import ConfigError, FunctionError, UnexpectedResponse, ConnectionError, FunctionTimeout


class Function(object):
    name = None
    host = None
    timeout = None
    exception_cls = None

    def __init__(self, name=None, host=None, timeout=None, exception_cls=None):
        if name is not None:
            self.name = name

        if host is not None:
            self.host = host

        if timeout is not None:
            self.timeout = timeout

        if exception_cls is not None:
            self.exception_cls = exception_cls

        if not self.name or not isinstance(self.name, six.string_types):
            raise ConfigError('Functions require a name argument')

    def call(self, **kwargs):
        res = self.send_request(**kwargs)
        return res.text

    def send_request(self, **kwargs):
        host = self.get_host()

        configured_functions = host.get_config().get('functions', None)

        if not configured_functions:
            raise ConfigError(
                '{} does not have any functions configured in {}'.format(
                    host.get_name(),
                    host.get_path_to_config_file(),
                )
            )

        if self.name not in configured_functions:
            raise ConfigError(
                '{}\'s config file does not contain a function named {}'.format(
                    host.get_name(),
                    host.get_path_to_config_file(),
                    self.name,
                )
            )

        serialized_data = self.serialize_data(kwargs)
        params = self.generate_params(serialized_data, kwargs)
        timeout = self.get_timeout()

        if settings.VERBOSITY >= FUNCTION_CALL:
            print(
                'Calling function "{}" with params {} and data {}'.format(
                    self.name,
                    params,
                    serialized_data,
                )
            )

        try:
            res = host.send_json_request(
                'function/{}'.format(self.name),
                params=params,
                data=serialized_data,
                timeout=timeout,
            )
        except RequestsConnectionError as e:
            raise six.reraise(ConnectionError, ConnectionError(*e.args), sys.exc_info()[2])
        except ReadTimeout as e:
            raise six.reraise(FunctionTimeout, FunctionTimeout(*e.args), sys.exc_info()[2])

        if res.status_code == 500:
            if self.exception_cls:
                raise self.exception_cls(res.text)

            raise FunctionError(
                '{name}: {res_text}'.format(
                    name=self.name,
                    res_text=res.text,
                )
            )

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Called function "{name}". {res_code}: {res_text}'.format(
                    name=self.name,
                    res_code=res.status_code,
                    res_text=res.text,
                )
            )

        return res

    def get_host(self):
        if self.host is None:
            # Default to using the singleton
            from .host import host
            self.host = host

        return self.host

    def get_name(self):
        return self.name

    @staticmethod
    def serialize_data(data):
        return json.dumps(data, cls=JSONEncoder)

    @staticmethod
    def generate_hash(content):
        content = content.encode('utf-8')
        return hashlib.sha1(content).hexdigest()

    def generate_params(self, serialized_data, data):
        return {
            'hash': self.generate_hash(serialized_data)
        }

    def get_timeout(self):
        if self.timeout:
            return self.timeout

        return settings.FUNCTION_TIMEOUT