# Django convenience hook to ensure that we can connect to the
# host during startup, rather than waiting for runtime checks

from .host import host

if not host.has_connected:
    host.connect()