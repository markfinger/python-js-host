import os
import js_host.conf
from js_host.verbosity import SILENT

js_host.conf.settings.configure(
    # The tests are invoked in the repo root, so we need to define SOURCE_ROOT
    SOURCE_ROOT=os.path.dirname(__file__),
    # Set the default config file
    CONFIG_FILE=os.path.join('config_files', 'host.config.js'),
    # Let the manager spin up instances for us
    USE_MANAGER=True,
    # Prevent js-host from outputting anything
    VERBOSITY=SILENT,
)