import time
import subprocess
from .base_server import BaseServer
from .conf import settings, Verbosity
from .exceptions import ErrorStartingProcess, UnexpectedResponse


class Manager(BaseServer):
    type_name = 'Manager'

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

        if settings.VERBOSITY >= Verbosity.PROCESS_START:
            print('Started {}'.format(self.get_name()))

    def stop(self):
        if self.is_running():
            res = self.send_request('shutdown', post=True)

            if res.status_code != 200:
                raise UnexpectedResponse(
                    'Attempted to shutdown host. {res_code}: {res_text}'.format(
                        res_code=res.status_code,
                        res_text=res.text,
                    )
                )

            if settings.VERBOSITY >= Verbosity.PROCESS_STOP:
                print('Stopped {}'.format(self.get_name()))

            # The request will end just before the process shuts down, so there is a tiny
            # possibility of a race condition. We delay as a precaution so that we can be
            # reasonably confident of the system's state.
            time.sleep(0.05)