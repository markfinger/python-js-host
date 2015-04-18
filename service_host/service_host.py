from .exceptions import ServiceError, UnexpectedResponse
from .base_class import BaseClass


class ServiceHost(BaseClass):
    type_name = 'Host'

    def send_request_to_service(self, service, data=None, cache_key=None):
        params = None
        if cache_key:
            params = {'cache-key': cache_key}

        # TODO: timeout
        res = self.send_request(
            'service/' + service,
            params=params,
            post=True,
            data=data,
            content_type='application/json'
        )

        if res.status_code == 500:
            raise ServiceError(
                '{service}: {res_text}'.format(
                    service=service,
                    res_text=res.text,
                )
            )

        if res.status_code != 200:
            raise UnexpectedResponse(
                'A request for service "{service}" responded with {res_code}: {res_text}'.format(
                    service=service,
                    res_code=res.status_code,
                    res_text=res.text,
                )
            )

        return res