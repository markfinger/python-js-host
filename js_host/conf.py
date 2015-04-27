import os
from optional_django import conf


class Verbosity(object):
    SILENT = 0
    # Output when connections are opened
    CONNECT = 100
    # Output when managers and managed hosts are started
    PROCESS_START = 200
    # Output when managers and managed hosts are sent `stop` signals
    PROCESS_STOP = 300
    # Output when functions are called
    FUNCTION_CALL = 400
    # Output everything
    ALL = 500


# TODO: move the internal docs into the README
class Conf(conf.Conf):
    django_namespace = 'JS_HOST'

    # A path that will resolve to a node binary
    PATH_TO_NODE = 'node'

    # An absolute path to the directory which contains your node_modules directory
    SOURCE_ROOT = None

    # A path to the binary used to control hosts and managers.
    # If the path is relative, it is appended to the SOURCE_ROOT setting
    BIN_PATH = os.path.join('node_modules', '.bin', 'js-host')

    # A path to the default config file used for hosts and managers.
    # If the path is relative, it is appended to the SOURCE_ROOT setting.
    CONFIG_FILE = 'host.config.js'

    # If True, the host will cache the output of the functions until it expires.
    # This can be overridden on functions by adding `cachable = False` to the
    # subclass of `Function`, or by adding `cache: false` to the config file's
    # object for that particular function
    CACHE = False

    # By default this will print to the terminal whenever processes are started or
    # connected to. If you want to suppress all output, set it to
    # `js_host.conf.Verbosity.SILENT`
    VERBOSITY = Verbosity.PROCESS_START

    FUNCTION_TIMEOUT = 10.0

    # Indicates that a manager should be used to spawn host instances
    # DO *NOT* USE THE MANAGER IN PRODUCTION
    USE_MANAGER = False

    # When the python process exits, the manager is informed to stop the host once this
    # timeout has expired. If the python process is only restarting, the manager will
    # cancel the timeout once it has reconnected. If the python process is shutting down
    # for good, the manager will stop the host's process shortly.
    ON_EXIT_STOP_MANAGED_HOSTS_AFTER = 10 * 1000  # 10 seconds

    # Once the js host has been configured, attempt to connect. This enables any
    # config or connection errors to be raised during startup, rather than runtime
    CONNECT_ONCE_CONFIGURED = True

    def configure(self, **kwargs):
        super(Conf, self).configure(**kwargs)

        if self.CONNECT_ONCE_CONFIGURED:
            # Ensure we can connect to the host
            from .host import host
            if not host.has_connected:
                host.connect()

settings = Conf()