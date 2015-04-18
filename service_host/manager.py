import json
import subprocess
import requests
import atexit
import time
from requests.exceptions import ConnectionError
from .service_host import ServiceHost
from .base_class import BaseClass
from .conf import settings, Verbosity


class ManagedServiceHost(ServiceHost):
    manager = None

    def __init__(self, *args, **kwargs):
        self.manager = kwargs.pop('manager')
        self.config = kwargs.pop('config')

        super(ManagedServiceHost, self).__init__(*args, **kwargs)

        # When the python process exits, we ask the manager to stop the
        # host after a timeout. If the python process is merely restarting,
        # the timeout will be cancelled when the next connection is opened.
        # If the python process is shutting down for good, we can ensure that
        # that the host's process will shut down inevitably.
        atexit.register(
            self.stop,
            timeout=60 * 1000  # 1 minute
        )

    def restart(self):
        self.stop()
        time.sleep(0.5)
        host = self.manager.start_managed_host(self.config_file)
        self.config = host.config

    def stop(self, timeout=None):
        self.manager.stop_managed_host(self.config_file, timeout)


class Manager(BaseClass):
    type_name = 'Manager'

    def connect(self):
        if not self.is_running():
            self.start()
        super(Manager, self).connect()

    def start(self):
        process = subprocess.Popen(
            (self.path_to_node, self.get_path_to_bin(), self.config_file, '--manager', '--detached'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        process.wait()

        stderr = process.stderr.read()
        if stderr:
            raise Exception(stderr)

        if not self.is_running():
            raise Exception('Failed to start manager')

        if settings.VERBOSITY >= Verbosity.PROCESS_START:
            print(
                'Started {type_name} at {url}'.format(
                    type_name=self.type_name,
                    url=self.get_url()
                )
            )

    def stop(self):
        pass

    def start_managed_host(self, config_file):
        if self.get_type_name() in (ServiceHost.type_name, ManagedServiceHost.type_name):
            raise Exception(
                (
                    'Trying to start a {type_name} at {url}, but a {current_type_name} is '
                    'already running at that address'
                ).format(
                    type_name=self.type_name,
                    current_type_name=self.get_type_name(),
                    url=self.get_url(),
                )
            )

        url = self.get_url('start')
        try:
            res = requests.post(url, params={'config': config_file})
        except ConnectionError:
            raise Exception(
                'Cannot connect to {type_name} at {url}'.format(
                    type_name=self.type_name,
                    url=url
                )
            )

        if res.status_code != 200:
            raise Exception(
                'Unexpected response when trying to start {type_name}: {res} - {res_text}'.format(
                    type_name=self.type_name,
                    res=res,
                    res_text=res.text
                )
            )

        host_json = res.json()

        started = host_json['started']
        config = json.loads(host_json['output'])

        if started and settings.VERBOSITY >= Verbosity.PROCESS_START:
            print(
                '{type_name} started {host_type_name} at http://{address}:{port}'.format(
                    type_name=self.type_name,
                    host_type_name=ManagedServiceHost.type_name,
                    address=config['address'],
                    port=config['port'],
                )
            )

        host = ManagedServiceHost(
            path_to_node=self.path_to_node,
            path_to_node_modules=self.path_to_node_modules,
            config_file=self.config_file,
            manager=self,
            config=config
        )

        return host

    def stop_managed_host(self, config_file, timeout=None):
        params = {'config': config_file}

        if timeout:
            params['timeout'] = timeout

        res = self.send_request('stop', params=params, post=True)

        if res.status_code != 200:
            raise Exception(
                'Failed to stop {host_type_name} with config {config_file} - {res_text}'.format(
                    host_type_name=ManagedServiceHost.type_name,
                    config_file=config_file,
                    res_text=res.text,
                )
            )

        if settings.VERBOSITY >= Verbosity.PROCESS_STOP:
            print(
                '{host_type_name} with config {config_file} will stop in {seconds} seconds '.format(
                    host_type_name=ManagedServiceHost.type_name,
                    config_file=config_file,
                    seconds=timeout / 1000 if timeout else 0,
                )
            )