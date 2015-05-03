import os
from optional_django import conf
from .verbosity import PROCESS_START
from .exceptions import ConfigError


class Conf(conf.Conf):
    django_namespace = 'JS_HOST'

    # An absolute path to the directory which contains your node_modules directory
    SOURCE_ROOT = os.getcwd()

    # A path to a default config file used for hosts and managers.
    # Relative paths are joined to SOURCE_ROOT
    CONFIG_FILE = 'host.config.js'

    # Indicates that a manager should be used to spawn host instances
    # DO *NOT* USE THE MANAGER IN PRODUCTION
    USE_MANAGER = False

    # A path that will resolve to a node binary
    PATH_TO_NODE = 'node'

    # A path to the binary used to control hosts and managers.
    # Relative paths are joined to SOURCE_ROOT
    BIN_PATH = os.path.join('node_modules', '.bin', 'js-host')

    # How long functions will wait for a response before raising errors
    FUNCTION_TIMEOUT = 10.0  # 10 seconds

    # If True, attempt to connect once js_host has been configured
    CONNECT_ONCE_CONFIGURED = True

    # An override for the root url used to send requests to a host.
    ROOT_URL = None

    # How verbose js-host should be about its actions
    VERBOSITY = PROCESS_START

    def configure(self, **kwargs):
        super(Conf, self).configure(**kwargs)

        if self.ROOT_URL:
            if self.USE_MANAGER:
                raise ConfigError(
                    'The ROOT_URL can not defined if USE_MANAGER is set to True. If you want to run a manager at a '
                    'different address or port, you should define the `address` and `port` properties in your config '
                    'file'
                )
            if self.ROOT_URL.endswith('/'):
                raise ConfigError(
                    'The ROOT_URL must not end in a slash. It should be an address in the format http://127.0.0.1:8000'
                )

        if self.CONNECT_ONCE_CONFIGURED:
            # Ensure that we raise connection issues during startup, rather than runtime
            from .host import host
            if not host.has_connected:
                host.connect()

settings = Conf()