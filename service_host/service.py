import hashlib
import json
from optional_django import six
from optional_django.serializers import JSONEncoder
from .conf import settings
from .exceptions import ConfigError


class Service(object):
    name = None
    host = None
    cacheable = True

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
            raise ConfigError('Services require a `name` attribute')

    def call(self, **kwargs):
        serialized_data = self.serialize_data(kwargs)

        cache_key = None
        if self.is_cacheable():
            cache_key = self.generate_cache_key(serialized_data, kwargs)

        return self.get_host().send_request_to_service(
            service=self.name,
            data=serialized_data,
            cache_key=cache_key
        )

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

            if 'services' not in host_config:
                raise ConfigError('Service host config is missing a `services` property')

            config = [obj for obj in host_config['services'] if 'name' in obj and obj['name'] == name]

            if len(config) == 0:
                raise ConfigError(
                    '{host_name} has no configured service matching "{name}"'.format(
                        host_name=host.get_name(),
                        name=name,
                    )
                )

            if len(config) > 1:
                raise ConfigError(
                    '{host_name} has multiple configured services matching {name}'.format(
                        host_name=host.get_name(),
                        name=name,
                    )
                )

            config = config[0]

            if not isinstance(config, dict):
                raise ConfigError(
                    'Service "{name}" cannot determine a config object from {config_file}'.format(
                        name=name,
                        config_file=host.config_file,
                    )
                )

            self.config = config

        return self.config

    def serialize_data(self, data):
        return json.dumps(data, cls=JSONEncoder)

    def is_cacheable(self):
        # Respect the global setting, the service's attribute, and the config file
        return settings.CACHE and self.cacheable and self.get_config().get('cache', True)

    def generate_cache_key(self, serialized_data, data):
        return hashlib.sha1(serialized_data).hexdigest()