from .service_host import ServiceHost
from .manager import Manager
from .managed_service_host import ManagedServiceHost


def singleton_host_and_manager(path_to_node, source_root, config_file, use_manager):
    conf = {
        'path_to_node': path_to_node,
        'source_root': source_root,
        'config_file': config_file,
    }

    if use_manager:
        manager = Manager(**conf)

        # Managers run as persistent processes, so it may already be running
        if not manager.is_running():
            manager.start()

        manager.connect()

        host = ManagedServiceHost(manager=manager)

        # Either start a managed host or connect to a pre-existing one
        host.start()
        host.connect()

        return host, manager

    host = ServiceHost(**conf)

    # In production environments, the host should be run as an external process
    # under a supervisor system. Hence, we only connect to it
    host.connect()

    return host, None