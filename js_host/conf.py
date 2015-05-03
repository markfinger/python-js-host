import os
from optional_django import conf
from .verbosity import PROCESS_START
from .exceptions import ConfigError


class Conf(conf.Conf):
    django_namespace = 'JS_HOST'

    # A path that will resolve to a node binary
    PATH_TO_NODE = 'node'

    # An absolute path to the directory which contains your node_modules directory
    SOURCE_ROOT = os.getcwd()

    # A path to the binary used to control hosts and managers.
    # Relative paths are joined to SOURCE_ROOT
    BIN_PATH = os.path.join('node_modules', '.bin', 'js-host')

    # A path to a default config file used for hosts and managers.
    # Relative paths are joined to SOURCE_ROOT
    CONFIG_FILE = 'host.config.js'

    # How long functions will wait for a response before raising errors
    FUNCTION_TIMEOUT = 10.0  # 10 seconds

    # Indicates that a manager should be used to spawn host instances
    # DO *NOT* USE THE MANAGER IN PRODUCTION
    USE_MANAGER = False

    # If True, attempt to connect once js_host has been configured
    CONNECT_ONCE_CONFIGURED = True

    # An override for the root url used to send requests to a host.
    URL_OVERRIDE = None

    # How verbose js-host should be about its actions
    VERBOSITY = PROCESS_START

    def configure(self, **kwargs):
        super(Conf, self).configure(**kwargs)

        if self.URL_OVERRIDE:
            if self.USE_MANAGER:
                raise ConfigError(
                    'The URL_OVERRIDE can not be used with USE_MANAGER set to True. If you want to run a manager at a '
                    'different address, you should define the `address` and `port` properties in your config file'
                )
            if self.URL_OVERRIDE.endswith('/'):
                raise ConfigError(
                    'The URL_OVERRIDE must not end in a slash. It should be an address in the format '
                    'http://127.0.0.1:8000'
                )

        if self.CONNECT_ONCE_CONFIGURED:
            # Ensure that we raise connection issues during startup, rather than runtime
            from .host import host
            if not host.has_connected:
                host.connect()

settings = Conf()