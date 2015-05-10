# Utils for spawning processes which interact with the `js-host` binary

import subprocess
import json
from .conf import settings
from .exceptions import ConfigError, ProcessError
from .utils import verbosity
from .manager import JSHostManager
from .js_host import JSHost


def read_status_from_config_file(config_file, extra_args=None):
    if settings.VERBOSITY >= verbosity.VERBOSE:
        print('Reading config file {}'.format(config_file))

    cmd = (settings.PATH_TO_NODE, settings.get_path_to_bin(), config_file, '--config',)

    if extra_args:
        cmd += extra_args

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()

    stderr = process.stderr.read()
    if stderr:
        raise ConfigError(stderr)

    stdout = process.stdout.read()
    stdout = stdout.decode('utf-8')

    return json.loads(stdout)


def spawn_detached_manager(config_file, status=None):
    if status is None:
        status = read_status_from_config_file(config_file, extra_args=('--manager',))

    manager = JSHostManager(status=status, config_file=config_file)

    process = subprocess.Popen(
        (settings.get_path_to_node(), settings.get_path_to_bin(), config_file, '--manager', '--detached'),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    process.wait()

    stderr = process.stderr.read()
    if stderr:
        if 'EADDRINUSE' in str(stderr):
            raise ProcessError(
                (
                    'Cannot start {} as another process is already running at its address. To run the process at '
                    'another address, you can set the `port` property of your host\'s config to a different number. If '
                    'the problem persists, this may be an indication of unstopped processes'
                ).format(manager.get_name())
            )
        raise ProcessError(stderr)

    stdout = process.stdout.read()
    stdout = stdout.decode('utf-8')

    new_status = json.loads(stdout)

    manager.status = new_status
    manager.validate_status()

    if not manager.is_running():
        raise ProcessError('Started {}, but cannot connect'.format(manager.get_name()))

    manager.connect()

    if settings.VERBOSITY >= verbosity.PROCESS_START:
        print('Started {}'.format(manager.get_name()))

    return manager


def spawn_managed_host(config_file, manager, connect_on_start=True):
    """
    Spawns a managed host, if it is not already running
    """

    data = manager.request_host_status(config_file)

    is_running = data['started']

    # Managed hosts run as persistent processes, so it may already be running
    if is_running:
        host_status = json.loads(data['host']['output'])
        logfile = data['host']['logfile']
    else:
        data = manager.start_host(config_file)
        host_status = json.loads(data['output'])
        logfile = data['logfile']

    host = JSHost(
        status=host_status,
        logfile=logfile,
        config_file=config_file,
        manager=manager
    )

    if not is_running and settings.VERBOSITY >= verbosity.PROCESS_START:
        print('Started {}'.format(host.get_name()))

    if connect_on_start:
        host.connect()

    return host