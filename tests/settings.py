import os
from service_host.conf import settings, Verbosity

PATH_TO_NODE = 'node'
PATH_TO_NODE_MODULES = os.path.join(os.path.dirname(__file__), 'node_modules')

settings.configure(
    VERBOSITY=Verbosity.ALL,
)