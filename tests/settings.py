import os
import js_host.conf
from js_host.verbosity import SILENT

js_host.conf.settings.configure(
    SOURCE_ROOT=os.path.dirname(__file__),

    # Set the default config file
    CONFIG_FILE=os.path.join('config_files', 'host.config.js'),

    # Let the manager spin up instances for us
    USE_MANAGER=True,

    # Force the managed hosts to stop when the python process has stopped
    ON_EXIT_STOP_MANAGED_HOSTS_AFTER=0,

    VERBOSITY=SILENT,
)