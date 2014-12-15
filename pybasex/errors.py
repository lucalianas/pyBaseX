class ConnectionError(Exception):
    pass


class ConnectionClosedError(Exception):
    pass


class ConfigurationError(Exception):
    pass


class UnknownDatabaseError(Exception):
    pass


class WrongURLError(Exception):
    pass