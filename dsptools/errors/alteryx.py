# pylint: disable = unnecessary-pass
class AlteryxEngineError(Exception):
    """
    Exception raised for errors related to Alteryx engine operations.

    This exception is used for errors encountered during the execution of Alteryx workflows
    or related operations.

    """

    pass


class AlteryxNotFound(Exception):
    """
    Exception raised when an Alteryx component or resource is not found.

    This exception is used to indicate that a specific Alteryx component, resource, or configuration is
    expected to exist but cannot be found.

    """

    pass


class NotAnAlteryxError(Exception):
    """
    Exception raised when an object is not of the expected Alteryx type.

    This exception is used to indicate that an object or component does not have the expected
    characteristics or type associated with Alteryx.

    """

    pass


class AlteryxLoggerError(Exception):
    """
    Exception raised for errors related to the Alteryx logging process.

    This exception is used for errors encountered during the logging process within Alteryx
    workflows or related operations.

    """

    pass


class AlteryxKillError(Exception):
    """
    Exception raised for errors related to the Alteryx process PID.

    This exception is used for errors encountered during the stop sequence
    of workflows or related operations.

    """

    pass
