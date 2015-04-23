# Exposes pre-configured singletons that the services use by default

from .conf import settings
from .service_host import ServiceHost
from .managed_service_host import ManagedServiceHost
from .manager import Manager

if settings.USE_MANAGER:
    manager = Manager()

    # Managers run as persistent processes, so it may already be running
    if not manager.is_running():
        manager.start()

    manager.connect()

    host = ManagedServiceHost(manager=manager)

    # Connect to a pre-existing host, or start one
    host.start()
    host.connect()
else:
    manager = None
    host = ServiceHost()

    # In production environments, the host should be run as an external process
    # under a supervisor system. Hence, we only connect to it
    host.connect()