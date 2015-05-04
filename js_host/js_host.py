import copy
import json
import atexit
import sys
from optional_django import six
from requests.exceptions import ConnectionError as RequestsConnectionError
from .conf import settings
from .exceptions import ProcessError, ConfigError
from .verbosity import DISCONNECT, PROCESS_START, PROCESS_STOP
from .base_server import BaseServer


class JSHost(BaseServer):
    expected_type_name = 'Host'

    # Generated at runtime for managed hosts
    manager = None
    logfile = None
    connection = None

    def __init__(self, *args, **kwargs):
        if 'manager' in kwargs:
            self.manager = kwargs.pop('manager')

            if 'config_file' in kwargs:
                self.config_file = kwargs.pop('config_file')
            else:
                # Reuse the manager's config so that we can avoid spinning up another process
                # just to read the config file. When a managed host starts or connects, it
                # overrides the config with the information returned from the manager
                self.config_file = self.manager.get_path_to_config_file()
                self.status = copy.deepcopy(self.manager.get_status())
                self.status['type'] = self.expected_type_name

        super(JSHost, self).__init__(*args, **kwargs)

    def start(self):
        if not self.manager:
            raise NotImplementedError('{} must be started manually'.format(self.get_name()))

        status = self.manager.request_host_status(self.get_path_to_config_file())

        if status['started']:
            raise ProcessError('{} has already started'.format(self.get_name()))

        data = self.manager.start_host(self.get_path_to_config_file())

        self.status = json.loads(data['output'])
        self.logfile = data['logfile']

        if settings.VERBOSITY >= PROCESS_START:
            print('Started {}'.format(self.get_name()))

    def stop(self, timeout=None, stop_manager_if_last=None):
        if not self.manager:
            raise NotImplementedError('{} must be stopped manually'.format(self.get_name()))

        self.manager.stop_host(self.get_path_to_config_file())

        if settings.VERBOSITY >= PROCESS_STOP:
            print('Stopped {}'.format(self.get_name()))

    def restart(self):
        if not self.manager:
            raise NotImplementedError('{} must be restarted manually'.format(self.get_name()))

        self.manager.restart_host(self.get_path_to_config_file())
        self.status = self.request_status()

    def connect(self):
        if self.manager:
            data = self.manager.request_host_status(self.get_path_to_config_file())
            if data['started']:
                self.status = json.loads(data['host']['output'])
                self.logfile = data['host']['logfile']

            if not self.connection:
                data = self.manager.open_connection_to_host(self.get_path_to_config_file())
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

        data = self.manager.close_connection_to_host(self.get_path_to_config_file(), self.connection)

        if data['started'] and settings.VERBOSITY >= DISCONNECT:
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