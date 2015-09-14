# Exposes convenience singletons which are configured, started, and connected

import copy
import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from .bin import read_status_from_config_file, spawn_detached_manager, spawn_managed_host
from .conf import settings
from .js_host import JSHost
from .manager import JSHostManager
from .exceptions import ConnectionError

config_file = settings.get_config_file()
status = read_status_from_config_file(config_file)

root_url = settings.ROOT_URL
if not root_url:
    root_url = 'http://{}:{}'.format(
        status['config']['address'],
        status['config']['port'],
    )

try:
    res = requests.get('{}/status'.format(root_url))
except RequestsConnectionError:
    res = None

if res and res.json() == status:
    manager = None

    host = JSHost(
        status=status,
        config_file=config_file,
        root_url = root_url
    )

    host.connect()
elif settings.USE_MANAGER:
    # Avoid re-reading the config file again by cloning and manually
    # editing the status object
    manager_status = copy.deepcopy(status)
    manager_status['type'] = JSHostManager.expected_type_name
    if 'functions' in manager_status:
        manager_status['functions'] = {}

    manager = JSHostManager(
        status=manager_status,
        config_file=config_file,
    )

    # Managers run as persistent processes, so it may already be running
    if manager.is_running():
        manager.connect()
    else:
        manager = spawn_detached_manager(
            config_file=config_file,
            status=manager_status,
        )

    host = spawn_managed_host(
        config_file=config_file,
        manager=manager
    )
else:
    raise ConnectionError('Cannot connect to JSHost at {}'.format(root_url))