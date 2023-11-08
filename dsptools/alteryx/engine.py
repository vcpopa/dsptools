from __future__ import annotations
from abc import ABC, abstractmethod
import warnings
from typing import Dict, Literal
import os
import subprocess
from sqlalchemy import create_engine
from dsptools.utils.execution import conditional_polling
from dsptools.alteryx.pid_utils import list_child_processes, check_pid, kill_pid
from dsptools.errors.alteryx import (
    AlteryxNotFound,
    NotAnAlteryxError,
    AlteryxEngineError,
    AlteryxLoggerError,
    AlteryxKillError,
)


class AlteryxEngineScaffold(ABC):
    @abstractmethod
    def run(self) -> True:
        pass

    @abstractmethod
    def stop(self) -> bool:
        pass

    @abstractmethod
    def log_to_sql(
        self, log_message: str, logging_level: Literal["INFO", "WARNING", "ERROR"]
    ) -> None:
        pass


class AlteryxEngine(AlteryxEngineScaffold):
    """
    Custom class for managing and running Alteryx workflows.

    Args:
        path_to_alteryx (str): Path to the Alteryx workflow file (.yxmd).
        log_to (Dict[str, str]): Logging settings for execution results.
        mode (Literal["PRODUCTION", "TEST", "RELEASE"]): Execution mode.
        verbose (bool, optional): Whether to print verbose messages. Defaults to False.

    Attributes:
        path_to_alteryx (str): Path to the Alteryx workflow file.
        log_to (Dict[str, str]): Logging settings for execution results.
        mode (Literal["PRODUCTION", "TEST", "RELEASE"]): Execution mode.
        verbose (bool): Whether to print verbose messages.
        process: Subprocess for running the Alteryx workflow.
        parent_pid: Process ID of the parent Alteryx process.
        child_pid: Process ID of the child Alteryx process.

    Raises:
        AlteryxNotFound: If the specified Alteryx workflow file does not exist.
        NotAnAlteryxError: If the specified file is not a valid Alteryx workflow.
        AttributeError: If the log_to parameter is not in the expected format.

    """

    def __init__(
        self,
        path_to_alteryx: str,
        log_to: Dict[str, str],
        mode: Literal["PRODUCTION", "TEST", "RELEASE"],
        verbose: bool = False,
    ) -> None:
        if not os.path.exists(path_to_alteryx):
            raise AlteryxNotFound("The specified file does not exist")
        if not path_to_alteryx.endswith(".yxmd"):
            raise NotAnAlteryxError(
                "The specified file is not a valid Alteryx workflow"
            )
        if "table" not in log_to.keys() or "connection_string" not in log_to.keys():
            raise AttributeError(
                f"The log_to parameter must be a dict with the following keys: 'table','connection_string'. You provided {', '.join(log_to.keys())}"
            )
        self.path_to_alteryx = path_to_alteryx
        self.log_to = log_to
        self.verbose = verbose
        self.mode = mode
        self.alteryx_name = f"""{os.path.basename(self.path_to_alteryx).replace(".yxmd", "")}_{self.mode}"""
        if self.verbose is True:
            print("Alteryx workflow initialized successfully. Ready to start")

    def run(self):
        """
        Start and run the Alteryx workflow.

        Starts the Alteryx process, monitors its output, and logs messages.

        """
        command = rf'"C:\Program Files\Alteryx\bin\AlteryxEngineCmd.exe" "{self.path_to_alteryx}"'

        if self.verbose is True:
            print("Alteryx is starting...")

        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        self.parent_pid = self.process.pid
        self.child_pid = conditional_polling(
            executable=list_child_processes,
            condition=check_pid,
            max_duration=120,
            interval=3,
            parent_pid=self.parent_pid,
        )
        while True:
            line = self.process.stdout.readline()
            line = (
                line.replace("'", "")
                .replace(",", "")
                .replace("\r", "")
                .replace("\n", "")
            )
            self.check_for_error_and_log_message(log_message=line)
            line = self.process.stderr.readline()
            line = (
                line.replace("'", "")
                .replace(",", "")
                .replace("\r", "")
                .replace("\n", "")
            )
            if not line:
                if self.verbose is True:
                    print("Alteryx workflow completed")
                break

            self.check_for_error_and_log_message(log_message=line)
            if self.verbose is True:
                print(line)

    def stop(self) -> None:
        """
        Stop the Alteryx workflow and kill associated processes.

        Terminates the Alteryx process and its child processes.

        Raises:
            AlteryxKillError: If any of the processes could not be killed.

        """
        killed_parent_pid = kill_pid(pid=self.parent_pid)
        if killed_parent_pid != self.parent_pid:
            self.log_to_sql(
                log_message=f"Parent PID {self.parent_pid} could not be killed",
                logging_level="ERROR",
            )
            raise AlteryxKillError(f"Parent PID {self.parent_pid} could not be killed")
        killed_child_pid = kill_pid(pid=self.child_pid)
        if killed_child_pid != self.child_pid:
            self.log_to_sql(
                log_message=f"Child PID {self.child_pid} could not be killed",
                logging_level="ERROR",
            )
            raise AlteryxKillError(f"Child PID {self.child_pid} could not be killed")
        self.log_to_sql(log_message="ALL PIDS HAVE BEEN KILLED", logging_level="INFO")

    def log_to_sql(
        self, log_message: str, logging_level: Literal["INFO", "WARNING", "ERROR"]
    ) -> None:
        """
        Log a message to a SQL database with the specified logging level.

        This method logs a message to a SQL database with the specified logging level ('INFO', 'WARNING', or 'ERROR').
        The log message includes the filename of the Alteryx workflow, the timestamp of the log entry, the message content,
        and the logging level.

        Args:
            log_message (str): The message to be logged to the SQL database.
            logging_level (Literal['INFO', 'WARNING', 'ERROR']): The logging level for the message.

        Raises:
            AlteryxLoggerError: If the specified logging level is not one of the supported levels ('INFO', 'WARNING', 'ERROR').
            AlteryxLoggerError: If the specified schema in self.log_to['table'] does not exist, preventing table creation.

        Warnings:
            UserWarning: If the log table specified in self.log_to['table'] does not exist, it will be created before logging.

        """

        # Check if the logging level is valid
        valid_logging_levels = {"INFO", "WARNING", "ERROR"}
        if logging_level not in valid_logging_levels:
            raise AlteryxLoggerError(
                f"Invalid logging level. Supported levels: {', '.join(valid_logging_levels)}"
            )

        # Extract schema and table from self.log_to['table']
        schema, table = self.log_to["table"].split(".", 1)
        con = create_engine(self.log_to["connection_string"]).raw_connection()
        with con.connect() as conn:
            # Check if the schema exists
            schema_exists_query = f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{schema}'"
            schema_exists = conn.execute(schema_exists_query).scalar() is not None

            if not schema_exists:
                raise AlteryxLoggerError(
                    f"Schema '{schema}' does not exist. Cannot create the log table."
                )

            # Check if the table exists
            table_exists_query = f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'"
            table_exists = conn.execute(table_exists_query).scalar() is not None

            if not table_exists:
                warnings.warn(
                    f"Log table '{self.log_to['table']}' was created!",
                    UserWarning,
                )
                # Log table doesn't exist, create it
                create_table_query = f"""
                    CREATE TABLE {self.log_to['table']} (
                        filename VARCHAR(255),
                        Created DATETIME,
                        Message TEXT,
                        LoggingLevel VARCHAR(10)
                    )
                """
                conn.execute(create_table_query)

            # Insert the log message
            insert_query = f"INSERT INTO {self.log_to['table']} (filename, Created, Message, LoggingLevel) VALUES ('{self.alteryx_name}', getdate(), '{log_message}', '{logging_level}')"
            conn.execute(insert_query)

    def check_for_error_and_log_message(self, log_message: str) -> None:
        """
        Check a log message for specific error conditions and log it to a SQL database.

        This method examines a log message for specific error conditions and logs them with the appropriate severity
        in a SQL database. If the message contains both 'error' and 'warning' keywords, it's logged as a warning.

        Args:
            log_message (str): The log message to be checked and logged.

        """
        # Convert the log message to lowercase for case-insensitive checks
        lower_message = log_message.lower()

        # Initialize error message and logging level
        error_message = f"Failure: {log_message}"
        logging_level = "INFO"

        # Check if the log message contains any error keywords
        if "error" in lower_message:
            logging_level = "ERROR"
            if "warning" in lower_message:
                logging_level = "WARNING"
                if self.verbose:
                    warnings.warn(log_message)
                    self.log_to_sql(
                        log_message=error_message, logging_level=logging_level
                    )
            else:
                if self.verbose:
                    warnings.warn(log_message)
                self.log_to_sql(log_message=error_message, logging_level=logging_level)
                raise AlteryxEngineError(
                    f"Exit raised by the following error: {error_message}"
                )
        else:
            # Log the message to a SQL database even if there's no error
            self.log_to_sql(log_message=log_message, logging_level=logging_level)
