# Exposes convenience singletons which are configured, connected, and started

from .conf import settings
from .js_host import JSHost
from .manager import JSHostManager

if settings.USE_MANAGER:
    manager = JSHostManager()

    # Managers run as persistent processes, so it may already be running
    if not manager.is_running():
        manager.start()

    manager.connect()

    host = JSHost(manager=manager)

    # Managed hosts run as persistent processes, so it may already be running
    if not host.is_running():
        host.start()

    host.connect()
else:
    manager = None
    host = JSHost()
    host.connect()