import hashlib
import json
from optional_django import six
from optional_django.serializers import JSONEncoder
from .conf import settings
from .exceptions import ConfigError


class Function(object):
    name = None
    host = None
    cacheable = True
    timeout = settings.FUNCTION_TIMEOUT

    # Read in from the config file
    config = None

    def __init__(self, name=None, host=None, cacheable=None):
        if name is not None:
            self.name = name

        if host is not None:
            self.host = host

        if cacheable is not None:
            self.cacheable = cacheable

        if not self.name or not isinstance(self.name, six.string_types):
            raise ConfigError('Functions require a `name`')

    def send_request(self, **kwargs):
        serialized_data = self.serialize_data(kwargs)

        cache_key = None
        if self.is_cacheable():
            cache_key = self.generate_cache_key(serialized_data, kwargs)

        return self.get_host().call_function(
            function=self.name,
            data=serialized_data,
            key=cache_key,
            timeout=self.timeout,
        )

    def call(self, **kwargs):
        res = self.send_request(**kwargs)
        return res.text

    def get_host(self):
        if not self.host:
            # Default to using the singleton
            from .host import host
            self.host = host

        return self.host

    def get_name(self):
        return self.name

    def get_config(self):
        if not self.config:
            name = self.get_name()

            host = self.get_host()
            host_config = host.get_config()

            if 'functions' not in host_config:
                raise ConfigError('Host config is missing a `functions` property')

            config = [obj for obj in host_config['functions'] if 'name' in obj and obj['name'] == name]

            if len(config) == 0:
                raise ConfigError(
                    '{host_name} has no configured function matching "{name}"'.format(
                        host_name=host.get_name(),
                        name=name,
                    )
                )

            if len(config) > 1:
                raise ConfigError(
                    '{host_name} has multiple configured functions matching {name}'.format(
                        host_name=host.get_name(),
                        name=name,
                    )
                )

            config = config[0]

            if not isinstance(config, dict):
                raise ConfigError(
                    'Function "{name}" cannot determine a config object from {config_file}'.format(
                        name=name,
                        config_file=host.config_file,
                    )
                )

            self.config = config

        return self.config

    def serialize_data(self, data):
        return json.dumps(data, cls=JSONEncoder)

    def is_cacheable(self):
        # Respect the global setting, the function's attribute, and the config file
        return settings.CACHE and self.cacheable and self.get_config().get('cache', True)

    def generate_cache_key(self, serialized_data, data):
        serialized_data = serialized_data.encode('utf-8')
        return hashlib.sha1(serialized_data).hexdigest()