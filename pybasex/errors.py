class ConnectionError(Exception):
    pass


class ConnectionClosedError(Exception):
    pass


class ConfigurationError(Exception):
    pass


class UnknownDatabaseError(Exception):
    pass


class InvalidURLError(Exception):
    pass


class OverwriteError(Exception):
    pass


class QueryError(Exception):
    pass


class AuthenticationError(Exception):
    pass