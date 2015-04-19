from optional_django import conf


class Verbosity(object):
    SILENT = 0
    CONNECT = 100  # Output when connections are opened
    PROCESS_START = 200  # Output when managers and managed hosts are started
    PROCESS_STOP = 300  # Output when managers and managed hosts are sent `stop` signals
    ALL = 1000  # Output everything


class Conf(conf.Conf):
    PRODUCTION = True
    PATH_TO_NODE = 'node'
    PATH_TO_NODE_MODULES = None
    VERBOSITY = Verbosity.PROCESS_START

    # Config file for the `service_host.host` singletons
    CONFIG_FILE = None

    # DO *NOT* USE THE MANAGER IN PRODUCTION
    USE_MANAGER = not PRODUCTION
    ON_EXIT_MANAGED_HOSTS_STOP_TIMEOUT = 60 * 1000  # 1 minute

settings = Conf()