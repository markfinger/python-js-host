class ConfigError(Exception):
    pass


class ConnectionError(Exception):
    pass


class ServiceError(Exception):
    pass


class ServiceTimeout(Exception):
    pass


class UnexpectedResponse(Exception):
    pass


class ErrorStartingProcess(Exception):
    pass