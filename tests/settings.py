import os
from js_host.conf import settings, Verbosity

settings.configure(
    SOURCE_ROOT=os.path.dirname(__file__),
    # Set the default config file
    CONFIG_FILE=os.path.join('config_files', 'host.config.js'),
    # Let the manager spin up instances for us
    USE_MANAGER=True,
    # Force the managed hosts to stop immediately once
    # the python process has stopped
    ON_EXIT_STOP_MANAGED_HOSTS_AFTER=0,
    VERBOSITY=Verbosity.SILENT,
)