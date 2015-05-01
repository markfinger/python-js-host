class ConfigError(Exception):
    pass


class ConnectionError(Exception):
    pass


class FunctionError(Exception):
    pass


class FunctionTimeout(Exception):
    pass


class UnexpectedResponse(Exception):
    pass


class ProcessError(Exception):
    pass