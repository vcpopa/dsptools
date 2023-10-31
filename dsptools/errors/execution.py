# pylint: disable = unnecessary-pass
class PollingTimeoutError(Exception):
    """
    Exception raised when a polling operation times out.

    This exception is used to indicate that a polling operation, which waits for a specific condition
    to be met, has exceeded the allowed time for waiting.

    """

    pass


class PollingExecutableError(Exception):
    """
    Exception raised when a polling executable encounters an error.

    This exception is used to handle errors occurring during the execution of a polling operation,
    such as errors in external executables or scripts used for polling.

    """

    pass


class PollingConditionError(Exception):
    """
    Exception raised when a polling condition is not met.

    This exception is used to indicate that the desired condition for polling, such as a particular
    state or event, is not met, and the polling operation cannot proceed.

    """

    pass


class RetryTimeout(Exception):
    """
    Exception raised when a retry operation times out.

    This exception is used to indicate that a retry operation, which attempts an action multiple times,
    has exceeded the allowed time for retrying.

    """

    pass


class TeamsMessageError(Exception):
    """
    Exception raised for errors related to sending messages to Microsoft Teams.

    This exception is used for errors encountered when sending messages or notifications to a
    Microsoft Teams channel or workspace.

    """

    pass
