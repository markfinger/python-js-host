import json
import atexit
import time
from .js_host import JSHost
from .conf import settings, Verbosity
from .exceptions import UnexpectedResponse


class ManagedJSHost(JSHost):
    manager = None

    def __init__(self, manager, config_file=None):
        self.manager = manager

        if config_file is not None:
            self.config_file = config_file
        else:
            # Reuse the manager's config to avoid the overhead of reading the file
            # again. Once the process has started, the real config is read in from
            # the process once it starts up
            self.config_file = self.manager.get_path_to_config_file()
            self.config = self.manager.get_config()

        super(ManagedJSHost, self).__init__(
            config_file=self.get_path_to_config_file(),
            source_root=manager.source_root,
            path_to_node=manager.path_to_node,
        )

    def start(self):
        """
        Connect to the manager and request a host using the host's config file.

        Managed hosts run on ports allocated by the OS and the manager is used
        to keep track of the ports used by each host. When we call host.start(),
        we ask the manager to start the host as a subprocess, only if it is not
        already running. Once the host is running, the manager returns the config
        used by the subprocess so that our host knows where to send requests
        """
        res = self.manager.send_request('start', params={'config': self.get_path_to_config_file()}, post=True)

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Attempted to start a {cls_name}: {res} - {res_text}'.format(
                    cls_name=type(self).__name__,
                    res=res,
                    res_text=res.text
                )
            )

        host_json = res.json()

        self.config = json.loads(host_json['output'])

        if host_json['started'] and settings.VERBOSITY >= Verbosity.PROCESS_START:
            print('Started {}'.format(self.get_name()))

        # When the python process exits, we ask the manager to stop the
        # host after a timeout. If the python process is merely restarting,
        # the timeout will be cancelled when the next connection is opened.
        # If the python process is shutting down for good, this enables some
        # assurance that the host's process will inevitably stop.
        atexit.register(
            self.stop,
            timeout=settings.ON_EXIT_STOP_MANAGED_HOSTS_AFTER,
        )

    def stop(self, timeout=None, stop_manager=None):
        """
        Stops a managed host.

        `timeout` specifies the number of milliseconds that the host will be
        stopped in. If `timeout` is provided, the method will complete while the
        host is still running

        `stop_manager` indicates that the manager should stop if this host is
        the last one being managed.
        """

        if not self.is_running():
            return

        params = {
            'config': self.get_path_to_config_file(),
        }

        if stop_manager is None:
            stop_manager = True

        if stop_manager:
            params['stop-manager-if-last-host'] = True

        if timeout:
            params['timeout'] = timeout

        res = self.manager.send_request('stop', params=params, post=True)

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Attempted to stop {name}. Response: {res_code}: {res_text}'.format(
                    name=self.get_name(),
                    res_code=res.status_code,
                    res_text=res.text,
                )
            )

        if not timeout:
            # The manager will stop the host after a few milliseconds, so we need to
            # ensure that the state of the system is as expected
            time.sleep(0.05)

        if settings.VERBOSITY >= Verbosity.PROCESS_STOP:
            if timeout:
                print(
                    '{name} will stop in {seconds} seconds'.format(
                        name=self.get_name(),
                        seconds=timeout / 1000.0,
                    )
                )
            else:
                print('Stopped {}'.format(self.get_name()))

    def restart(self):
        self.stop(stop_manager=False)
        self.start()
        self.connect()