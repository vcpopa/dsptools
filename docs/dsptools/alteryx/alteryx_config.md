Module dsptools.alteryx.alteryx_config
======================================

Functions
---------


`run_alteryx_from_config(config_path: str) ‑> None`
:   Run Alteryx based on the configuration provided in a YAML file.

    Args:
        config_path (str): The path to the configuration YAML file.

    Raises:
        ValueError: If the configuration YAML is invalid or missing required fields.

Classes
-------

`AlteryxConfigModel(**data: Any)`
:   Model for the Alteryx configuration.

    Args:
        path_to_alteryx (str): The path to the Alteryx workflow file (.yxmd).
        mode (Literal["PRODUCTION", "TESTING", "RELEASE"]): The execution mode of the Alteryx workflow.
        admins (List[str]): A list of administrators for the Alteryx workflow.
        flow_execution (FlowExecution): Optional flow execution settings.
        log_to (LogTo): Logging settings.

    Raises:
        ValueError: If the 'path_to_alteryx' does not end with '.yxmd'.
        ValueError: If 'flow_execution' is specified but does not contain 'timeout_settings' or 'error_handling_settings'.
        ValueError: If 'timeout_settings' is specified but does not contain 'on_timeout' or 'timeout_duration'.
        ValueError: If 'error_handling_settings' is specified but does not contain 'on_error'.

    Create a new model by parsing and validating input data from keyword arguments.

    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel
    * pydantic.utils.Representation

    ### Class variables

    `admins: List[str]`
    :

    `flow_execution: Optional[None]`
    :

    `log_to: dsptools.alteryx.alteryx_config.LogTo`
    :

    `mode: Literal['PRODUCTION', 'TESTING', 'RELEASE']`
    :

    `path_to_alteryx: str`
    :

    ### Static methods

    `validate_flow_execution(value)`
    :

    `validate_path_to_alteryx(path)`
    :

`ErrorHandlingSettings(**data: Any)`
:   Model for specifying error handling settings in the configuration.

    Args:
        on_error (Literal["skip", "warn", "raise"]): The action to take when an exception occurs.

    Create a new model by parsing and validating input data from keyword arguments.

    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel
    * pydantic.utils.Representation

    ### Class variables

    `on_error: Literal['skip', 'warn', 'raise']`
    :

`FlowExecution(**data: Any)`
:   Model for specifying flow execution settings in the configuration.

    Args:
        error_handling_settings (ErrorHandlingSettings): Error handling settings for the flow execution.
        timeout_settings (TimeoutSettings): Timeout settings for the flow execution.

    Create a new model by parsing and validating input data from keyword arguments.

    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel
    * pydantic.utils.Representation

    ### Class variables

    `error_handling_settings: Optional[dsptools.alteryx.alteryx_config.ErrorHandlingSettings]`
    :

    `timeout_settings: Optional[dsptools.alteryx.alteryx_config.TimeoutSettings]`
    :

`LogTo(**data: Any)`
:   Model for specifying logging settings in the configuration.

    Args:
        table (str): The table to log execution results to.
        connection_string (str): The connection string for logging.

    Create a new model by parsing and validating input data from keyword arguments.

    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel
    * pydantic.utils.Representation

    ### Class variables

    `connection_string: str`
    :

    `table: str`
    :

`TimeoutSettings(**data: Any)`
:   Model for specifying timeout settings in the configuration.

    Args:
        on_timeout (Literal["skip", "warn", "raise"]): The action to take when a timeout occurs.
        timeout_duration (int): The maximum execution time allowed for the decorated function, in seconds.

    Create a new model by parsing and validating input data from keyword arguments.

    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * pydantic.main.BaseModel
    * pydantic.utils.Representation

    ### Class variables

    `on_timeout: Literal['skip', 'warn', 'raise']`
    :

    `timeout_duration: int`
    :