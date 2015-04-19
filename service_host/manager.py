import sys
import subprocess
import json
from optional_django import six
from .base_server import BaseServer
from .conf import settings, Verbosity
from .exceptions import ErrorStartingProcess


class Manager(BaseServer):
    type_name = 'Manager'

    def start(self):
        try:
            output = subprocess.check_output(
                # TODO: managers should accept a flag to stop when their last host stops
                (self.path_to_node, self.get_path_to_bin(), self.config_file, '--manager', '--detached'),
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError, e:
            raise six.reraise(ErrorStartingProcess, ErrorStartingProcess(*e.args), sys.exc_info()[2])

        config = json.loads(output)

        if not self.is_running():
            raise ErrorStartingProcess('Failed to start manager')

        if settings.VERBOSITY >= Verbosity.PROCESS_START:
            print('Started {}'.format(self.get_name()))

    def stop(self):
        # TODO: send request to /shutdown
        pass