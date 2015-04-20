import sys
from optional_django import six
from requests.exceptions import ConnectionError as RequestsConnectionError, ReadTimeout
from .exceptions import ServiceError, UnexpectedResponse, ConnectionError, ServiceTimeout
from .base_server import BaseServer


class ServiceHost(BaseServer):
    type_name = 'Host'

    def start(self):
        raise NotImplementedError('{} must be started manually started'.format(self.get_name()))

    def stop(self):
        raise NotImplementedError('{} must be stopped manually'.format(self.get_name()))

    def send_request_to_service(self, service, data=None, cache_key=None, timeout=None):
        if not self.has_connected:
            raise ConnectionError('{} has not connected'.format(self.get_name()))

        params = {}
        if cache_key:
            params['cache-key'] = cache_key

        try:
            res = self.send_request(
                'service/' + service,
                params=params,
                headers={'content-type': 'application/json'},
                post=True,
                data=data,
                timeout=timeout,
            )
        except RequestsConnectionError, e:
            raise six.reraise(ConnectionError, ConnectionError(*e.args), sys.exc_info()[2])
        except ReadTimeout, e:
            raise six.reraise(ServiceTimeout, ServiceTimeout(*e.args), sys.exc_info()[2])

        if res.status_code == 500:
            raise ServiceError(
                '{service}: {res_text}'.format(
                    service=service,
                    res_text=res.text,
                )
            )

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Called service "{name}". {res_code}: {res_text}'.format(
                    name=service,
                    res_code=res.status_code,
                    res_text=res.text,
                )
            )

        return res