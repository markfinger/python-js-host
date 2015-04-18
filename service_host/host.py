from .conf import settings
from .service_host import ServiceHost
from .manager import Manager

kwargs = {
    'path_to_node': settings.PATH_TO_NODE,
    'path_to_node_modules': settings.PATH_TO_NODE_MODULES,
    'config_file': settings.CONFIG_FILE,
}

if settings.USE_MANAGER:
    manager = Manager(**kwargs)
    host = manager.start_managed_host(settings.CONFIG_FILE)
else:
    host = ServiceHost(**kwargs)