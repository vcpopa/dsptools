Module dsptools.errors.execution
================================

Classes
-------

`PollingConditionError(*args, **kwargs)`
:   Exception raised when a polling condition is not met.
    
    This exception is used to indicate that the desired condition for polling, such as a particular
    state or event, is not met, and the polling operation cannot proceed.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException

`PollingExecutableError(*args, **kwargs)`
:   Exception raised when a polling executable encounters an error.
    
    This exception is used to handle errors occurring during the execution of a polling operation,
    such as errors in external executables or scripts used for polling.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException

`PollingTimeoutError(*args, **kwargs)`
:   Exception raised when a polling operation times out.
    
    This exception is used to indicate that a polling operation, which waits for a specific condition
    to be met, has exceeded the allowed time for waiting.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException

`RetryTimeout(*args, **kwargs)`
:   Exception raised when a retry operation times out.
    
    This exception is used to indicate that a retry operation, which attempts an action multiple times,
    has exceeded the allowed time for retrying.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException

`TeamsMessageError(*args, **kwargs)`
:   Exception raised for errors related to sending messages to Microsoft Teams.
    
    This exception is used for errors encountered when sending messages or notifications to a
    Microsoft Teams channel or workspace.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException