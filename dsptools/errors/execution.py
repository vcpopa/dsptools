class PollingTimeoutError(Exception):
    pass


class PollingExecutableError(Exception):
    pass


class PollingConditionError(Exception):
    pass


class RetryTimeout(Exception):
    pass


class TeamsMessageError(Exception):
    pass
