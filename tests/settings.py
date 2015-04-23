import os
from service_host.conf import settings

settings.configure(
    SOURCE_ROOT=os.path.dirname(__file__),
    # Set the default config file
    CONFIG_FILE=os.path.join(os.path.dirname(__file__), 'config_files', 'services.config.js'),
    # Let the manager spin up instances for us
    USE_MANAGER=True,
    # Force the managed hosts to stop immediately once
    # the python process has stopped
    ON_EXIT_STOP_MANAGED_HOSTS_AFTER=0,
)