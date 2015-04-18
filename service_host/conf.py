from optional_django import conf


class Verbosity(object):
    SILENT = 0
    CONNECT = 100
    PROCESS_START = 200
    PROCESS_STOP = 300
    VERBOSE = 1000


class Conf(conf.Conf):
    PATH_TO_NODE = 'node'
    PATH_TO_NODE_MODULES = None
    CONFIG_FILE = None
    USE_MANAGER = False
    VERBOSITY = Verbosity.PROCESS_START

settings = Conf()