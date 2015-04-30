import os
from optional_django import conf
from .verbosity import PROCESS_START


class Conf(conf.Conf):
    django_namespace = 'JS_HOST'

    # A path that will resolve to a node binary
    PATH_TO_NODE = 'node'

    # An absolute path to the directory which contains your node_modules directory
    SOURCE_ROOT = None

    # A path to the binary used to control hosts and managers.
    BIN_PATH = os.path.join('node_modules', '.bin', 'js-host')

    # A path to a default config file used for hosts and managers.
    CONFIG_FILE = 'host.config.js'

    # How long functions will wait for response before raising errors
    FUNCTION_TIMEOUT = 10.0  # 10 seconds

    # Indicates that a manager should be used to spawn host instances
    # DO *NOT* USE THE MANAGER IN PRODUCTION
    USE_MANAGER = False

    # How long should managed hosts run for, once the python process has stopped
    ON_EXIT_STOP_MANAGED_HOSTS_AFTER = 5 * 1000  # 5 seconds

    # If True, attempt to connect once js_host has been configured
    CONNECT_ONCE_CONFIGURED = True

    # How verbose processes should be about their actions
    VERBOSITY = PROCESS_START

    def configure(self, **kwargs):
        super(Conf, self).configure(**kwargs)

        if self.CONNECT_ONCE_CONFIGURED:
            # Ensure we can connect to the host
            from .host import host
            if not host.has_connected:
                host.connect()

settings = Conf()