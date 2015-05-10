from distutils.spawn import find_executable
import os
from optional_django import conf
from .utils.verbosity import PROCESS_START
from .exceptions import ConfigError


class Conf(conf.Conf):
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
    PATH_TO_BIN = os.path.join('node_modules', 'js-host', 'bin', 'js-host.js')

    # How long functions will wait for a response before raising errors
    FUNCTION_TIMEOUT = 10.0  # 10 seconds

    # If True, attempt to connect once js_host has been configured
    CONNECT_ONCE_CONFIGURED = True

    # An override for the root url used to send requests to a host.
    ROOT_URL = None

    # How verbose js-host should be about its actions
    VERBOSITY = PROCESS_START

    # Flags to indicate that particular values have been checked. They are used
    # to prevents us from hitting the filesystem repeatedly
    _validated = {}

    def configure(self, **kwargs):
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

        super(Conf, self).configure(**kwargs)

        if self.CONNECT_ONCE_CONFIGURED:
            # Ensure that we raise connection issues during startup, rather than runtime
            from .host import host
            if not host.has_connected:
                host.connect()

    def get_path_to_node(self):
        path = self.PATH_TO_NODE

        if 'PATH_TO_NODE' not in self._validated and not find_executable(path):
            raise ConfigError(
                (
                    'Executable "{}" does not exist. Please define the PATH_TO_NODE setting in '
                    'js_host.conf.settings'
                ).format(path)
            )
        self._validated['PATH_TO_NODE'] = True

        return path

    def get_source_root(self):
        path = self.SOURCE_ROOT

        if 'SOURCE_ROOT' not in self._validated and not os.path.isdir(path):
            raise ConfigError('Source root {} does not exist or is not a directory'.format(path))
        self._validated['SOURCE_ROOT'] = True

        return path

    def get_path_to_bin(self):
        if os.path.isabs(self.PATH_TO_BIN):
            path = self.PATH_TO_BIN
        else:
            path = os.path.join(self.SOURCE_ROOT, self.PATH_TO_BIN)

        if 'PATH_TO_BIN' not in self._validated and not os.path.isfile(path):
            raise ConfigError('js-host binary {} does not exist'.format(path))
        self._validated['PATH_TO_BIN'] = True

        return path

    def get_config_file(self):
        if os.path.isabs(self.CONFIG_FILE):
            path = self.CONFIG_FILE
        else:
            path = os.path.join(self.SOURCE_ROOT, self.CONFIG_FILE)

        if 'CONFIG_FILE' not in self._validated and not os.path.isfile(path):
            raise ConfigError('Config file {} does not exist'.format(path))
        self._validated['CONFIG_FILE'] = True

        return path

    def get_root_url(self):
        return self.ROOT_URL

settings = Conf()