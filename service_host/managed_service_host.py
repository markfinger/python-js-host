import json
import atexit
import time
from .service_host import ServiceHost
from .conf import settings, Verbosity
from .exceptions import UnexpectedResponse


class ManagedServiceHost(ServiceHost):
    manager = None

    def __init__(self, manager):
        self.manager = manager
        self.config = manager.get_config()
        super(ManagedServiceHost, self).__init__(
            path_to_node=manager.path_to_node,
            path_to_node_modules=manager.path_to_node_modules,
            config_file=manager.config_file
        )

    def start(self):
        res = self.manager.send_request('start', params={'config': self.config_file})

        if res.status_code != 200:
            raise UnexpectedResponse(
                'Attempted to start a managed host: {res} - {res_text}'.format(
                    name=self.get_name(),
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
            timeout=settings.ON_EXIT_MANAGED_HOSTS_STOP_TIMEOUT,
        )

    def stop(self, timeout=None):
        params = {'config': self.config_file}

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

        if settings.VERBOSITY >= Verbosity.PROCESS_STOP:
            print(
                '{name} will stop in {seconds} seconds'.format(
                    name=self.get_name(),
                    seconds=timeout / 1000 if timeout else 0,
                )
            )

        # The manager stops hosts asynchronously, so we need to delay
        # to ensure that the state of the system is as expected
        time.sleep(0.15)

    def restart(self):
        self.stop()
        self.start()
        self.connect()