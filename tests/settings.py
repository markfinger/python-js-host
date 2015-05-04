import os
from js_host import verbosity

SECRET_KEY = '_'

INSTALLED_APPS = (
    'js_host',
)

# When run under nose, the settings are bound in tests/__init__.py
# When run under django, js_host/models.py imports the settings
JS_HOST = {
    # The tests are invoked in the repo root, so we need to define SOURCE_ROOT
    'SOURCE_ROOT': os.path.dirname(__file__),
    # Set the default config file
    'CONFIG_FILE': os.path.join('config_files', 'host.config.js'),
    # Let the manager spin up instances for us
    'USE_MANAGER': True,
    # Prevent js-host from outputting anything
    'VERBOSITY': verbosity.SILENT,
}