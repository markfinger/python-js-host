import time
import sys
import subprocess
from optional_django import six
from .base_server import BaseServer
from .conf import settings, Verbosity
from .exceptions import ErrorStartingProcess, UnexpectedResponse


class Manager(BaseServer):
    type_name = 'Manager'

    def start(self):
        try:
            subprocess.check_output(
                # TODO: managers should accept a flag to stop when their last host stops
                (self.path_to_node, self.get_path_to_bin(), self.config_file, '--manager', '--detached'),
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError, e:
            raise six.reraise(ErrorStartingProcess, ErrorStartingProcess(*e.args), sys.exc_info()[2])

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