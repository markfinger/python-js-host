# Django hook to connect during startup

from .conf import settings

if settings.CONNECT_ONCE_CONFIGURED:
    from .host import host
    if not host.has_connected:
        host.connect()
