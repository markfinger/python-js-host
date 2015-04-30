import atexit
import time
import subprocess
import json
from .base_server import BaseServer
from .conf import settings
from .verbosity import PROCESS_START, PROCESS_STOP
from .exceptions import ErrorStartingProcess, UnexpectedResponse


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
            raise ErrorStartingProcess(stderr)

        if not self.is_running():
            raise ErrorStartingProcess('Failed to start manager')

        if settings.VERBOSITY >= PROCESS_START:
            print('Started {}'.format(self.get_name()))

    def stop(self):
        if self.is_running():
            res = self.send_request('manager/stop', post=True)

            if res.status_code != 200:
                raise UnexpectedResponse(
                    'Attempted to stop host. {res_code}: {res_text}'.format(
                        res_code=res.status_code,
                        res_text=res.text,
                    )
                )

            if settings.VERBOSITY >= PROCESS_STOP:
                print('Stopped {}'.format(self.get_name()))

            # The request will end just before the process stop, so there is a tiny
            # possibility of a race condition. We delay as a precaution so that we
            # can be reasonably confident of the system's state.
            time.sleep(0.05)

    def restart(self):
        raise NotImplementedError()

    def start_host(self, config_file):
        """
        Connect to the manager and request a host using the host's config file.

        Managed hosts run on ports allocated by the OS and the manager is used
        to keep track of the ports used by each host. We ask the manager to start
        the host as a subprocess, only if it is not already running. Once the
        host is running, the manager returns information so that the host knows
        where to send requests
        """
        res = self.send_request('host/start', params={'config': config_file}, post=True)

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Attempted to start a JSHost: {res} - {res_text}'.format(
                    res=res,
                    res_text=res.text
                )
            )

        host = res.json()

        host['status'] = json.loads(host['output'])

        # When the python process exits, we ask the manager to stop the
        # host after a timeout. If the python process is merely restarting,
        # the timeout will be cancelled when the next connection is opened.
        # If the python process is shutting down for good, this enables some
        # assurance that the host's process will inevitably stop.
        atexit.register(
            self.stop_host,
            config_file=config_file,
            timeout=settings.ON_EXIT_STOP_MANAGED_HOSTS_AFTER,
        )

        return host

    def stop_host(self, config_file, timeout=None, stop_if_last=None):
        """
        Stops a managed host specified by `config_file`.

        `timeout` specifies the number of milliseconds that the host will be
        stopped in. If `timeout` is provided, the method will complete while the
        host is still running

        `stop_if_last` indicates that the manager should stop if this host is
        the last one being managed.
        """

        if not self.is_running():
            return False

        params = {
            'config': config_file,
        }

        if stop_if_last is None:
            stop_if_last = True

        if stop_if_last:
            params['stop-manager-if-last-host'] = True

        if timeout:
            params['timeout'] = timeout

        res = self.send_request('host/stop', params=params, post=True)

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Attempted to stop JSHost. Response: {res_code}: {res_text}'.format(
                    res_code=res.status_code,
                    res_text=res.text,
                )
            )

        if not timeout:
            # The manager will stop the host after a few milliseconds, so we need to
            # ensure that the state of the system is as expected
            time.sleep(0.05)

        return True