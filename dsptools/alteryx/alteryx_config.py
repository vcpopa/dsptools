# pylint:disable=no-self-argument
# pylint:disable=consider-alternative-union-syntax
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, validator

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
    def validate_connstring(cls,connection_string: str) -> str:
        if "mssql+pyodbc:///?odbc_connect=" not in connection_string:
            raise ValueError("Not a valid connection string")
        return connection_string


class AlteryxConfigModel(BaseModel):
    """
    Model for the Alteryx configuration.

    Args:
        path_to_alteryx (str): The path to the Alteryx workflow file (.yxmd).
        mode (Literal["PRODUCTION", "TESTING", "RELEASE"]): The execution mode of the Alteryx workflow.
        admins (list[str]): A list of administrators for the Alteryx workflow.
        flow_execution (FlowExecution): Optional flow execution settings.
        log_to (LogTo): Logging settings.

    Raises:
        ValueError: If the 'path_to_alteryx' does not end with '.yxmd'.
        ValueError: Ifd 'mode' not one of 'PRODUCTION','TESTTING','RELEASE'.
    """

    path_to_alteryx: str
    mode: Literal["PRODUCTION", "TESTING", "RELEASE"]
    admins: list[str]
    log_to: LogTo

    @validator("path_to_alteryx")
    def validate_path_to_alteryx(cls, path):
        if not path.endswith(".yxmd"):
            raise ValueError("path_to_alteryx must end with '.yxmd'")
        return path

    @validator("mode"):
    def validate_mode(cls,mode):
        if mode not in ['PRODUCTION','TESTTING','RELEASE']:
            raise ValueError("'mode' must be one of 'PRODUCTION','TESTTING','RELEASE'")
        return mode