from typing import List, Union, Literal
import yaml
from pydantic import BaseModel, validator
from dsptools.alteryx.engine import AlteryxEngine
from dsptools.errors.alteryx import AlteryxEngineError
from dsptools.utils.execution import handle_failure, timeout


class TimeoutSettings(BaseModel):
    """
    Model for specifying timeout settings in the configuration.

    Args:
        on_timeout (Literal["skip", "warn", "raise"]): The action to take when a timeout occurs.
        timeout_duration (int): The maximum execution time allowed for the decorated function, in seconds.
    """

    on_timeout: Literal["skip", "warn", "raise"]
    timeout_duration: int


class ErrorHandlingSettings(BaseModel):
    """
    Model for specifying error handling settings in the configuration.

    Args:
        on_error (Literal["skip", "warn", "raise"]): The action to take when an exception occurs.
    """

    on_error: Literal["skip", "warn", "raise"]


class FlowExecution(BaseModel):
    """
    Model for specifying flow execution settings in the configuration.

    Args:
        error_handling_settings (ErrorHandlingSettings): Error handling settings for the flow execution.
        timeout_settings (TimeoutSettings): Timeout settings for the flow execution.
    """

    error_handling_settings: Union[ErrorHandlingSettings, None]
    timeout_settings: Union[TimeoutSettings, None]


class LogTo(BaseModel):
    """
    Model for specifying logging settings in the configuration.

    Args:
        table (str): The table to log execution results to.
        connection_string (str): The connection string for logging.
    """

    table: str
    connection_string: str


class AlteryxConfigModel(BaseModel):
    """
    Model for the Alteryx configuration.

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
    """

    path_to_alteryx: str
    mode: Literal["PRODUCTION", "TESTING", "RELEASE"]
    admins: List[str]
    flow_execution: Union[None, FlowExecution]
    log_to: LogTo

    @validator("path_to_alteryx")
    def validate_path_to_alteryx(cls, path):
        if not path.endswith(".yxmd"):
            raise ValueError("path_to_alteryx must end with '.yxmd'")
        return path

    @validator("flow_execution", pre=True)
    def validate_flow_execution(cls, value):
        if value is not None:
            if (
                "timeout_settings" not in value
                and "error_handling_settings" not in value
            ):
                raise ValueError(
                    "At least one of 'timeout_settings' or 'error_handling_settings' must be specified in 'flow_execution'."
                )
            if "timeout_settings" in value:
                timeout_settings = value["timeout_settings"]
                if (
                    "on_timeout" not in timeout_settings
                    or "timeout_duration" not in timeout_settings
                ):
                    raise ValueError(
                        "Both 'on_timeout' and 'timeout_duration' must be specified in 'timeout_settings'."
                    )
            if "error_handling_settings" in value:
                error_handling_settings = value["error_handling_settings"]
                if "on_error" not in error_handling_settings:
                    raise ValueError(
                        "'on_error' must be specified in 'error_handling_settings'."
                    )
        return value


def run_alteryx_from_config(config_path: str) -> None:
    """
    Run Alteryx based on the configuration provided in a YAML file.

    Args:
        config_path (str): The path to the configuration YAML file.

    Raises:
        ValueError: If the configuration YAML is invalid or missing required fields.
    """
    # Load the configuration from the YAML file
    with open(config_path) as f:
        config_data = yaml.safe_load(f)

    try:
        config = AlteryxConfigModel(**config_data)
    except pydantic.error_wrappers.ValidationError as e:
        raise ValueError(f"Invalid configuration: {e.errors()}")

    # Extract configuration data using square brackets for dictionary access
    path_to_alteryx = config["path_to_alteryx"]
    log_to = config["log_to"]
    admins = config["admins"]
    mode = config["mode"]

    # Create an AlteryxEngine instance
    alteryx_flow = AlteryxEngine(
        path_to_alteryx=path_to_alteryx, log_to=log_to, mode=mode
    )

    flow_execution = config["flow_execution"]
    if not flow_execution:
        # If no flow execution settings are provided, run Alteryx without timeouts or error handling
        alteryx_flow.run()
    else:
        # Extract flow execution settings using square brackets
        catch_errors_enabled = True
        timeout_enabled = True
        on_error = "skip"
        on_timeout='warn'
        error_handling_settings = flow_execution["error_handling_settings"]
        timeout_settings = flow_execution["timeout_settings"]
        if error_handling_settings is None:
            catch_errors_enabled = False
        else:
            on_error = error_handling_settings["on_error"]
        if timeout_settings is None:
            timeout_enabled = False
        else:
            on_timeout = timeout_settings["on_timeout"]
            timeout_duration = timeout_settings["timeout_duration"]

        # Define a function that runs Alteryx with specified error handling and timeouts
        @handle_failure(
            handle=[AlteryxEngineError], on_error=on_error, enabled=catch_errors_enabled
        )
        @timeout(
            max_timeout=timeout_duration, on_timeout=on_timeout, enabled=timeout_enabled
        )
        def run_wrapper(alteryx: AlteryxEngine) -> None:
            alteryx.run()

        # Run Alteryx with the specified settings
        run_wrapper(alteryx=alteryx_flow)
