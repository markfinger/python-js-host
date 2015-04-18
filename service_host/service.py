import json
from optional_django.serializers import JSONEncoder


class Service(object):
    name = None
    host = None

    def __init__(self):
        if not self.name:
            raise Exception('Services require a name')

        host_config = self.get_host().get_config()

        if (
            'services' not in host_config or
            self.name not in [service.get('name', None) for service in host_config['services']]
        ):
            raise Exception('Service host has not been configured to use service "{}"'.format(self.name))

    def get_host(self):
        if self.host:
            return self.host

        from .host import host
        self.host = host

        return self.host

    def call(self, data=None, cache_key=None):
        host = self.get_host()
        serialized_data = json.dumps(data, cls=JSONEncoder)
        return host.send_request_to_service(
            service=self.name,
            data=serialized_data,
            cache_key=cache_key
        )

