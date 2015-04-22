# Exposes pre-configured singletons that the services use by default

from .conf import settings
from .utils import singleton_host_and_manager
from .exceptions import ConfigError

if not settings.PATH_TO_NODE:
    raise ConfigError('service_host requires the PATH_TO_NODE setting to be defined')

if not settings.SOURCE_ROOT:
    raise ConfigError('service_host requires the SOURCE_ROOT setting to be defined')

if not settings.CONFIG_FILE:
    raise ConfigError('service_host requires the CONFIG_FILE setting to be defined')

host, manager = singleton_host_and_manager(
    path_to_node=settings.PATH_TO_NODE,
    source_root=settings.SOURCE_ROOT,
    config_file=settings.CONFIG_FILE,
    use_manager=settings.USE_MANAGER,
)