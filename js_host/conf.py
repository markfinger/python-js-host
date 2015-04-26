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

    # An absolute path to the directory containing the node_modules directory
    # that js-host was installed into
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

    """
    DO *NOT* USE THE MANAGER IN PRODUCTION
    --------------------------------------

    If set to True, a manager process will be used to start and stop host processes.
    The manager runs at the port used by the config - either the defined or default
    one - and whenever a request comes in to start a host, it will either start
    it up or simply inform the python process where to find it.

    Do *not* use the manager in production, it exists purely to solve issues relating
    to the typical development environment:

    - Many of the typical JS functions involve processes which have an initial overhead,
     but are performant after the first run, compilers are the usual example. Using a
     persistent process enables functions to maintain a warm cache of the project's
     assets.

    - Running a persistent node process involves manually starting a node process
     with the proper incantation, which adds unwanted overhead on staff that are not
     familiar with the technology.

    - If the node process is started programmatically as a child of the python process,
     it will be need to be restarted with the the python process. Given the frequent
     restarts of python development servers, this delays the immediate feedback
     resulting from code changes.

    - If you run the node process as a detached child, this introduces additional
     overheads as you need to ensure that the process is inevitably stopped. The
     manager does this automatically, once a connection has been closed for a
     certain time period.

    The manager comes with certain downsides:

    - It complicates the process of getting access to the stdout/stderr of either the
     manager or the host. Hence, if the host goes down outside of a request cycle,
     there is no indication as to the reasons why.
    - The manager runs the host on a pseudo-random port allocated by the OS, this
     introduces an unlikely - but technically possible - opportunity for a port collision
     to occur.

    If you wish to avoid these issues, you can simply run the host as a normal process,
    by calling `node node_modules/.bin/js-host host.config.js`, which
    will run a host directly, and allow you to view the host's stdout and stderr.
    """
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