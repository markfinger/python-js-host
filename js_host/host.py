# Exposes configured and started singletons that the Function
# instances use by default

from .conf import settings
from .js_host import JSHost
from .js_host_manager import JSHostManager

if settings.USE_MANAGER:
    manager = JSHostManager()

    # Managers run as persistent processes, so it may already be running
    if not manager.is_running():
        manager.start()

    manager.connect()

    host = JSHost(manager=manager)
    host.start()
    host.connect()
else:
    manager = None
    host = JSHost()
    host.connect()