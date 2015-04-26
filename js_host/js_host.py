import sys
from optional_django import six
from requests.exceptions import ConnectionError as RequestsConnectionError, ReadTimeout
from .conf import settings, Verbosity
from .exceptions import JSFunctionError, UnexpectedResponse, ConnectionError, JSFunctionTimeout
from .base_server import BaseServer


class JSHost(BaseServer):
    type_name = 'Host'

    def start(self):
        raise NotImplementedError('{} must be started manually started'.format(self.get_name()))

    def stop(self):
        raise NotImplementedError('{} must be stopped manually'.format(self.get_name()))

    def call_function(self, function, data=None, key=None, timeout=None):
        if not self.has_connected:
            raise ConnectionError('{} has not connected'.format(self.get_name()))

        params = {}
        if key:
            params['key'] = key

        if settings.VERBOSITY >= Verbosity.FUNCTION_CALL:
            print(
                'Calling function "{}" with data {}{}'.format(
                    function,
                    data,
                    'and key {}'.format(key) if key else ''
                )
            )

        try:
            res = self.send_request(
                'function/' + function,
                params=params,
                headers={'content-type': 'application/json'},
                post=True,
                data=data,
                timeout=timeout,
            )
        except RequestsConnectionError as e:
            raise six.reraise(ConnectionError, ConnectionError(*e.args), sys.exc_info()[2])
        except ReadTimeout as e:
            raise six.reraise(JSFunctionTimeout, JSFunctionTimeout(*e.args), sys.exc_info()[2])

        if res.status_code == 500:
            raise JSFunctionError(
                '{function}: {res_text}'.format(
                    function=function,
                    res_text=res.text,
                )
            )

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Called function "{function}". {res_code}: {res_text}'.format(
                    function=function,
                    res_code=res.status_code,
                    res_text=res.text,
                )
            )

        return res