import os
from js_host.utils import verbosity

TEST_ROOT = os.path.dirname(__file__)

SECRET_KEY = '_'

INSTALLED_APPS = (
    'js_host',
)


class ConfigFiles(object):
    MISSING = os.path.join(os.path.dirname(__file__), 'config_files', '__non_existent_file__')
    EMPTY = os.path.join(os.path.dirname(__file__), 'config_files', 'empty.host.config.js')
    BASE_SERVER = os.path.join(os.path.dirname(__file__), 'config_files', 'test_base_server.host.config.js')
    BASE_JS = os.path.join(os.path.dirname(__file__), 'config_files', 'base_js_host_tests.host.config.js')
    NO_FUNCTIONS = os.path.join(os.path.dirname(__file__), 'config_files', 'no_functions.host.config.js')
    MANAGED_HOST_LIFECYCLE = os.path.join(
        os.path.dirname(__file__), 'config_files', 'test_managed_js_host_lifecycle.host.config.js'
    )
    MANAGER = os.path.join(os.path.dirname(__file__), 'config_files', 'test_manager.host.config.js')
    MANAGER_LIFECYCLE = os.path.join(
        os.path.dirname(__file__), 'config_files', 'test_manager_lifecycle.host.config.js'
    )
    JS_HOST = os.path.join(os.path.dirname(__file__), 'config_files', 'test_js_host.host.config.js')


# When run under nose, the settings are bound in tests/__init__.py
# When run under django, js_host/models.py imports the settings
JS_HOST = {
    # The tests are invoked in the repo root, so we need to define SOURCE_ROOT
    'SOURCE_ROOT': TEST_ROOT,
    # Set the default config file
    'CONFIG_FILE': os.path.join('config_files', 'default.host.config.js'),
    # Let the manager spin up instances for us
    'USE_MANAGER': True,
    # Prevent js-host from outputting anything
    'VERBOSITY': verbosity.SILENT,
}


