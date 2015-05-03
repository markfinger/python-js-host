import time
import subprocess
from optional_django import six
from .base_server import BaseServer
from .conf import settings
from .verbosity import PROCESS_START, PROCESS_STOP
from .exceptions import ProcessError, UnexpectedResponse


class JSHostManager(BaseServer):
    expected_type_name = 'Manager'
    read_config_file_params = ('--manager',)

    def start(self):
        process = subprocess.Popen(
            (self.path_to_node, self.get_path_to_bin(), self.get_path_to_config_file(), '--manager', '--detached'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        process.wait()

        stderr = process.stderr.read()
        if stderr:
            if six.b('EADDRINUSE') in stderr:
                raise ProcessError(
                    (
                        '{} is attempting to run at an address already in use. To run the process at another address, '
                        'you can set the `port` property of your host\'s config to a different number. If the problem '
                        'persists, this is an indication of unstopped processes and/or version mismatches'
                    ).format(self.get_name())
                )
            raise ProcessError(stderr)

        if not self.is_running():
            raise ProcessError('Failed to start manager')

        if settings.VERBOSITY >= PROCESS_START:
            print('Started {}'.format(self.get_name()))

    def stop(self):
        """
        If the manager is running, tell it to stop its process
        """
        res = self.send_request('manager/stop', post=True)

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Attempted to stop manager. {res_code}: {res_text}'.format(
                    res_code=res.status_code,
                    res_text=res.text,
                )
            )

        if settings.VERBOSITY >= PROCESS_STOP:
            print('Stopped {}'.format(self.get_name()))

        # The request will end just before the process stops, so there is a tiny
        # possibility of a race condition. We delay as a precaution so that we
        # can be reasonably confident of the system's state.
        time.sleep(0.05)

    def restart(self):
        raise NotImplementedError()

    def request_host_status(self, config_file):
        res = self.send_json_request('host/status', data={'config': config_file})

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Attempted to check a managed JSHost\'s status: {res} - {res_text}'.format(
                    res=res,
                    res_text=res.text
                )
            )

        return res.json()

    def start_host(self, config_file):
        """
        Connect to the manager and request a host using the host's config file.

        Managed hosts run on ports allocated by the OS and the manager is used
        to keep track of the ports used by each host. We ask the manager to start
        the host as a subprocess, only if it is not already running. Once the
        host is running, the manager returns information so that the host knows
        where to send requests
        """
        res = self.send_json_request('host/start', data={'config': config_file})

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Attempted to start a JSHost: {res} - {res_text}'.format(
                    res=res,
                    res_text=res.text
                )
            )

        return res.json()

    def stop_host(self, config_file):
        """
        Stops a managed host specified by `config_file`.
        """
        res = self.send_json_request('host/stop', data={'config': config_file})

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Attempted to stop a JSHost. Response: {res_code}: {res_text}'.format(
                    res_code=res.status_code,
                    res_text=res.text,
                )
            )

        return res.json()

    def restart_host(self, config_file):
        """
        Restarts a managed host specified by `config_file`.
        """

        res = self.send_json_request('host/restart', data={'config': config_file})

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Attempted to restart a JSHost. Response: {res_code}: {res_text}'.format(
                    res_code=res.status_code,
                    res_text=res.text,
                )
            )

        return res.json()

    def open_connection_to_host(self, config_file):
        res = self.send_json_request('host/connect', data={'config': config_file})

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Attempted to open a connection to a managed JSHost. Response: {res_code}: {res_text}'.format(
                    res_code=res.status_code,
                    res_text=res.text,
                )
            )

        return res.json()

    def close_connection_to_host(self, config_file, connection):
        res = self.send_json_request(
            'host/disconnect',
            data={
                'config': config_file,
                'connection': connection,
            },
        )

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Attempted to close a connection to a managed JSHost. Response: {res_code}: {res_text}'.format(
                    res_code=res.status_code,
                    res_text=res.text,
                )
            )

        return res.json()