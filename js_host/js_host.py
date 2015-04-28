from .conf import settings
from .verbosity import PROCESS_START, PROCESS_STOP
from .base_server import BaseServer


class JSHost(BaseServer):
    type_name = 'Host'
    manager = None

    def __init__(self, *args, **kwargs):
        if 'manager' in kwargs:
            self.manager = kwargs.pop('manager')

            if 'config_file' in kwargs:
                self.config_file = kwargs.pop('config_file')
            else:
                # Reuse the manager's config to avoid the overhead of reading the file
                # again. Once the process has started, the real config is read in from
                # the process once it starts up
                self.config_file = self.manager.get_path_to_config_file()
                self.config = self.manager.get_config()

        super(JSHost, self).__init__(*args, **kwargs)

    def start(self):
        if not self.manager:
            raise NotImplementedError('{} must be started manually'.format(self.get_name()))

        host = self.manager.start_host(self.get_path_to_config_file())

        self.config = host['config']

        if host['started'] and settings.VERBOSITY >= PROCESS_START:
            print('Started {}'.format(self.get_name()))

    def stop(self, timeout=None, stop_manager_if_last=None):
        if not self.manager:
            raise NotImplementedError('{} must be stopped manually'.format(self.get_name()))

        stopped = self.manager.stop_host(self.get_path_to_config_file(), stop_if_last=stop_manager_if_last)

        if stopped and settings.VERBOSITY >= PROCESS_STOP:
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
        self.stop(stop_manager_if_last=False)
        self.start()
        self.connect()