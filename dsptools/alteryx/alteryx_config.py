# pylint:disable=no-self-argument
# pylint:disable=no-name-in-module
from __future__ import annotations
import os
from typing import Literal
from pydantic import BaseModel, validator
import yaml
from dsptools.alteryx.engine import AlteryxEngine
from dsptools.utils.notifications import send_email
from dsptools.errors.execution import PollingTimeoutError
from dsptools.errors.alteryx import (
    AlteryxEngineError,
    AlteryxKillError,
    AlteryxLoggerError,
    AlteryxNotFound,
    NotAnAlteryxError,
)


class LogTo(BaseModel):
    """
    Model for specifying logging settings in the configuration.

    Args:
        table (str): The table to log execution results to.
        connection_string (str): The connection string for logging.
    """

    table: str
    connection_string: str

    @validator("connection_string")
    def validate_connstring(cls, connection_string: str, values) -> dict:
        if "mssql+pyodbc:///?odbc_connect=" not in connection_string:
            raise ValueError("Not a valid connection string")

        log_to_dict = {
            "table": values.get("table"),
            "connection_string": connection_string,
        }
        return log_to_dict


class AlteryxConfigModel(BaseModel):
    """
    Model for the Alteryx configuration.

    Args:
        path_to_alteryx (str): The path to the Alteryx workflow file (.yxmd).
        mode (Literal["PRODUCTION", "TESTING", "RELEASE"]): The execution mode of the Alteryx workflow.
        admins (list[str]): A list of administrators for the Alteryx workflow.
        log_to (LogTo): Logging settings.
        on_error (Literal["ignore", "warn", "raise"]): The behavior on error.
        verbose (bool): Whether to enable verbose mode.

    Raises:
        ValueError: If the 'path_to_alteryx' does not end with '.yxmd'.
        ValueError: If 'mode' is not one of 'PRODUCTION', 'TESTING', 'RELEASE'.
        ValueError: If 'on_error' is not one of 'ignore', 'warn', 'raise'.
    """

    path_to_alteryx: str
    mode: Literal["PRODUCTION", "TESTING", "RELEASE"]
    admins: list[str]
    log_to: LogTo
    on_error: Literal["ignore", "warn", "raise"]
    verbose: bool = True  # Fix the default value

    @validator("path_to_alteryx")
    def validate_path_to_alteryx(cls, path):
        if not path.endswith(".yxmd"):
            raise ValueError("path_to_alteryx must end with '.yxmd'")
        if not os.path.exists(path):
            raise AlteryxNotFound("Could not find Alteryx path")
        return path

    @validator("mode")
    def validate_mode(cls, mode):
        if mode not in ["PRODUCTION", "TESTING", "RELEASE"]:
            raise ValueError("'mode' must be one of 'PRODUCTION', 'TESTING', 'RELEASE'")
        return mode

    @validator("on_error")
    def validate_on_error(cls, on_error):
        if on_error not in ["ignore", "warn", "raise"]:
            raise ValueError("'on_error' must be one of 'ignore', 'warn', 'raise'")
        return on_error


def run_alteryx_from_config_file(config_path: str, **kwargs):
    """
    Run an Alteryx workflow based on the configuration file and handle exceptions.

    Args:
        config_path (str): Path to the configuration file.
        **kwargs: Additional arguments, such as 'email_inbox' and 'email_pwd'.

    """
    # Load configuration from file
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    config_model = AlteryxConfigModel(
        path_to_alteryx=config["path_to_alteryx"],
        log_to=config["log_to"],
        mode=config["mode"],
        on_error=config["on_error"],
        admins=config["admins"],
        verbose=config["verbose"],
    )

    try:
        # Start the Alteryx Engine
        log_to_dict = {
            "table": config_model.log_to.table,
            "connection_string": config_model.log_to.connection_string,
        }
        alteryx_engine = AlteryxEngine(
            path_to_alteryx=config_model.path_to_alteryx,
            log_to=log_to_dict,
            mode=config_model.mode,
            verbose=config_model.verbose,
        )
        runner = alteryx_engine.run()
        if runner == 0:
            subject = f"{alteryx_engine.alteryx_name} - COMPLETED"
            message = ""
        else:
            subject = f"{alteryx_engine.alteryx_name} ERROR - invalid return code"
            message = f"{alteryx_engine.alteryx_name} has finished but the process was returned with code {runner}"
        if "email_inbox" in kwargs and "email_pwd" in kwargs:
            send_email(
                emails=config_model.admins,
                subject=subject,
                message=message,
                email_inbox=kwargs["email_inbox"],
                email_pwd=kwargs["email_pwd"],
            )
    except AlteryxNotFound as e:
        # Handle AlteryxNotFound exception
        subject = f"{alteryx_engine.alteryx_name} ERROR - FILE NOT FOUND"
        message = f"{alteryx_engine.alteryx_name} encountered an error: {e}"
        if "email_inbox" in kwargs and "email_pwd" in kwargs:
            send_email(
                emails=config_model.admins,
                subject=subject,
                message=message,
                email_inbox=kwargs["email_inbox"],
                email_pwd=kwargs["email_pwd"],
            )
        raise AlteryxNotFound from e

    except NotAnAlteryxError as e:
        # Handle NotAnAlteryxError exception
        subject = f"{alteryx_engine.alteryx_name} ERROR - NOT A VALID FILE"
        message = f"{alteryx_engine.alteryx_name} encountered an error: {e}"
        if "email_inbox" in kwargs and "email_pwd" in kwargs:
            send_email(
                emails=config_model.admins,
                subject=subject,
                message=message,
                email_inbox=kwargs["email_inbox"],
                email_pwd=kwargs["email_pwd"],
            )
        raise AlteryxNotFound from e

    except PollingTimeoutError as e:
        # Handle PolllingTimeout
        subject = f"{alteryx_engine.alteryx_name} ERROR - ALTERYX FAILED TO START"
        message = f"{alteryx_engine.alteryx_name} COULD NOT SPAWN A CHILD PROCESS: {e}"
        if "email_inbox" in kwargs and "email_pwd" in kwargs:
            send_email(
                emails=config_model.admins,
                subject=subject,
                message=message,
                email_inbox=kwargs["email_inbox"],
                email_pwd=kwargs["email_pwd"],
            )
        raise e from e

    except (AlteryxEngineError, AlteryxLoggerError) as e:
        # Handle other exceptions
        if config_model.on_error == "ignore":
            pass
        else:
            if "email_inbox" in kwargs and "email_pwd" in kwargs:
                subject = f"{alteryx_engine.alteryx_name} ERROR"
                message = f"{alteryx_engine.alteryx_name} encountered an error: {e} . DEFAULT BEHAVIOR ON ERROR: {config_model.on_error}"
                send_email(
                    emails=config_model.admins,
                    subject=subject,
                    message=message,
                    email_inbox=kwargs["email_inbox"],
                    email_pwd=kwargs["email_pwd"],
                )
                if "raise" in config_model.on_error:
                    # Stop Alteryx and re-raise the exception
                    stop_wrapper(
                        alteryx_engine=alteryx_engine,
                        config_model=config_model,
                        *kwargs,
                    )
                    raise e from e


def stop_wrapper(
    alteryx_engine: AlteryxEngine, config_model: AlteryxConfigModel, **kwargs
):
    """
    Stop the Alteryx Engine and handle exceptions if the stop operation fails.

    Args:
        alteryx_engine (AlteryxEngine): The AlteryxEngine instance.
        config_model (AlteryxConfigModel): The configuration model.
        **kwargs: Additional arguments, such as 'email_inbox' and 'email_pwd'.

    """
    try:
        # Stop the Alteryx Engine
        alteryx_engine.stop()
    except AlteryxKillError as e:
        # Handle AlteryxKillError exception
        if "email_inbox" in kwargs and "email_pwd" in kwargs:
            subject = f"{alteryx_engine.alteryx_name} STOP FAILURE"
            message = f"""{alteryx_engine.alteryx_name} COULD NOT BE STOPPED: {e} . MANUAL INTERVENTION REQUIRED. KILL THE PROCESS BY RUNNING:
            'taskkill /F /PID {alteryx_engine.parent_pid}' for the parent process
            AND
            'taskkill /F /PID {alteryx_engine.child_pid}' for the child process
            """
            send_email(
                emails=config_model.admins,
                subject=subject,
                message=message,
                email_inbox=kwargs["email_inbox"],
                email_pwd=kwargs["email_pwd"],
            )
            raise e from e
