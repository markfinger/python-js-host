# Exposes pre-configured singletons that the functions use by default

from .conf import settings
from .js_host import JSHost
from .managed_js_host import ManagedJSHost
from .manager import Manager

if settings.USE_MANAGER:
    manager = Manager()

    # Managers run as persistent processes, so it may already be running
    if not manager.is_running():
        manager.start()

    manager.connect()

    host = ManagedJSHost(manager=manager)

    host.start()
    host.connect()
else:
    manager = None
    host = JSHost()

    # In production environments, the host should be run as an external process
    # under a supervisor system. Hence, we only connect to it
    host.connect()