import os
from service_host.conf import settings

settings.configure(
    SOURCE_ROOT=os.path.dirname(__file__),
    CONFIG_FILE=os.path.join(os.path.dirname(__file__), 'config_files', 'services.config.js'),
    USE_MANAGER=True,
    # Force the managed hosts to stop immediately
    ON_EXIT_STOP_MANAGED_HOSTS_AFTER=1,  # 1 millisecond
)