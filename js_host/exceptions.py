class ConfigError(Exception):
    pass


class ConnectionError(Exception):
    pass


class JSFunctionError(Exception):
    pass


class JSFunctionTimeout(Exception):
    pass


class UnexpectedResponse(Exception):
    pass


class ErrorStartingProcess(Exception):
    pass