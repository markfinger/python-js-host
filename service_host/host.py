from .conf import settings
from .utils import singleton_host_and_manager

# Convenience singletons that service.Service instances will use by default
host, manager = singleton_host_and_manager(
    path_to_node=settings.PATH_TO_NODE,
    path_to_node_modules=settings.PATH_TO_NODE_MODULES,
    config_file=settings.CONFIG_FILE,
    use_manager=settings.USE_MANAGER,
)