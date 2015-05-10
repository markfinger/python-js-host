import atexit
import sys
from requests.exceptions import ConnectionError as RequestsConnectionError
from .conf import settings
from .exceptions import ProcessError
from .utils import six, verbosity
from .base_server import BaseServer


class JSHost(BaseServer):
    expected_type_name = 'Host'

    manager = None
    logfile = None
    connection = None

    def __init__(self, manager=None, logfile=None, *args, **kwargs):
        self.manager = manager
        self.logfile = logfile

        super(JSHost, self).__init__(*args, **kwargs)

    def stop(self):
        if not self.manager:
            raise NotImplementedError('{} must be stopped manually'.format(self.get_name()))

        self.manager.stop_host(self.config_file)

        if settings.VERBOSITY >= verbosity.PROCESS_STOP:
            print('Stopped {}'.format(self.get_name()))

    def restart(self):
        if not self.manager:
            raise NotImplementedError('{} must be restarted manually'.format(self.get_name()))

        self.manager.restart_host(self.config_file)
        self.status = self.request_status()

    def connect(self):
        if self.manager:
            if not self.connection:
                data = self.manager.open_connection_to_host(self.config_file)
                self.connection = data['connection']

            # Ensure that the connection is closed once the python
            # process has exited
            atexit.register(self.disconnect)

        super(JSHost, self).connect()

    def disconnect(self):
        if not self.manager:
            raise NotImplementedError('Only managed hosts can disconnect'.format(self.get_name()))

        if not self.connection or not self.manager.is_running():
            return

        data = self.manager.close_connection_to_host(self.config_file, self.connection)

        if data['started'] and settings.VERBOSITY >= verbosity.DISCONNECT:
            message = 'Closed connection to {} - {}'.format(self.get_name(), self.connection)
            if data['stopTimeout']:
                message += '. Host will stop in {} seconds unless another connection is opened'.format(
                    data['stopTimeout'] / 1000.0
                )
            print(message)

        self.connection = None

    def send_request(self, *args, **kwargs):
        """
        Intercept connection errors which suggest that a managed host has
        crashed and raise an exception indicating the location of the log
        """
        try:
            return super(JSHost, self).send_request(*args, **kwargs)
        except RequestsConnectionError as e:
            if (
                self.manager and
                self.has_connected and
                self.logfile and
                'unsafe' not in kwargs
            ):
                raise ProcessError(
                    '{} appears to have crashed, you can inspect the log file at {}'.format(
                        self.get_name(),
                        self.logfile,
                    )
                )
            raise six.reraise(RequestsConnectionError, RequestsConnectionError(*e.args), sys.exc_info()[2])