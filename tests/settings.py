import os
from service_host.conf import settings

settings.configure(
    PATH_TO_NODE_MODULES=os.path.join(os.path.dirname(__file__), 'node_modules'),
    CONFIG_FILE=os.path.join(os.path.dirname(__file__), 'config_files', 'services.config.js'),
    USE_MANAGER=True,
    # Force the managed hosts to stop immediately
    ON_EXIT_STOP_MANAGED_HOSTS_AFTER=1,  # 1 millisecond
)