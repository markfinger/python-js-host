import os
from service_host.conf import settings, Verbosity

settings.configure(
    VERBOSITY=Verbosity.SILENT,
    PATH_TO_NODE_MODULES=os.path.join(os.path.dirname(__file__), 'node_modules'),
    CONFIG_FILE=os.path.join(os.path.dirname(__file__), 'config_files', 'services.config.js'),
    USE_MANAGER=True,
)