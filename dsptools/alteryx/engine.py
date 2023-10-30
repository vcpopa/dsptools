from abc import ABC, abstractmethod
from typing import Dict, Literal
import os
import subprocess
import yaml
from sqlalchemy import create_engine
import warnings
from dsptools.errors.alteryx import (
    AlteryxNotFound,
    NotAnAlteryxError,
    AlteryxEngineError,
    AlteryxLoggerError,
)


class AlteryxEngineScaffold(ABC):
    @abstractmethod
    def run(self) -> True:
        pass

    @abstractmethod
    def stop(self) -> bool:
        pass

    @abstractmethod
    def log_to_sql(self) -> None:
        pass


class AlteryxEngine(AlteryxEngineScaffold):
    """
    Represents an Alteryx Engine for executing Alteryx workflows.

    This class allows you to interact with Alteryx workflows and control their execution.

    Args:
        path_to_alteryx (str): The path to the Alteryx workflow file (.yxmd).
        log_to (Dict[str, str]): A dictionary containing information on where to log the execution results. It should include the keys 'table' and 'connection_string'.
        admins (List[str], optional): A list of admin usernames. Required if 'on_error' is set to 'warn'. Defaults to None.
        on_error (Literal['ignore', 'warn', 'raise'], optional): The action to take on workflow errors. Must be one of 'ignore', 'warn', or 'raise'. Defaults to 'raise'.
        verbose (bool, optional): Whether to enable verbose output. Defaults to False.

    Raises:
        AlteryxNotFound: If the specified Alteryx workflow file does not exist.
        NotAnAlteryxError: If the specified file is not a valid Alteryx workflow.
        AttributeError: If the 'on_error' value, 'admins', or 'log_to' dictionary are invalid.

    Example:
        engine = AlteryxEngine(
            path_to_alteryx="workflow.yxmd",
            log_to={"table": "log_table", "connection_string": "your_connection_string"},
            admins=["admin1", "admin2"],
            on_error="warn",
            verbose=True
        )
    """

    def __init__(
        self,
        path_to_alteryx: str,
        log_to: Dict[str, str],
        mode: Literal["PRODUCTION", "TEST", "RELEASE"],
        verbose: bool = False,
    ) -> None:
        """
        Initialize a new AlteryxEngine instance.

        Args:
            path_to_alteryx (str): The path to the Alteryx workflow file (.yxmd). It is recommended to use the absolute path to avoid execution errors.
            log_to (Dict[str, str]): A dictionary containing information on where to log the execution results.
                It should include the keys 'table' and 'connection_string'.
            mode (Literal['PRODUCTION', 'TEST', 'RELEASE']): The execution mode for Alteryx, must be one of 'PRODUCTION', 'TEST', or 'RELEASE'.
            verbose (bool, optional): Whether to enable verbose output. Defaults to False.

        Returns:
            None

        Raises:
            AlteryxNotFound: If the specified Alteryx workflow file does not exist.
            NotAnAlteryxError: If the specified file is not a valid Alteryx workflow.
            AttributeError: If the 'log_to' dictionary is missing keys or if 'mode' is not one of the allowed modes.

        Note:
            The 'mode' parameter specifies the execution mode of the Alteryx workflow. You should choose one of the following modes:
            - 'PRODUCTION': Use this mode for production execution.
            - 'TEST': Use this mode for testing purposes.
            - 'RELEASE': Use this mode for a final release.

        Example:
            engine = AlteryxEngine(
                path_to_alteryx='/path/to/your/workflow.yxmd',
                log_to={'table': 'output_table', 'connection_string': 'your_database_connection'},
                mode='PRODUCTION',
                verbose=True
            )
        """
        # Constructor implementation here
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
        if self.verbose is True:
            print("Alteryx flow initialized successfully. Ready to start")

    def run(self):
        """
        Run the Alteryx workflow specified by path_to_alteryx.

        This method initiates the execution of the Alteryx workflow specified by 'path_to_alteryx' by calling
        the Alteryx Engine command-line tool. It captures the workflow's execution logs, checks for errors, and logs
        the messages based on the specified logging settings.

        Returns:
            None

        """
        command = r'"C:\Program Files\Alteryx\bin\AlteryxEngineCmd.exe" "{}"'.format(
            self.path_to_alteryx
        )
        if self.verbose is True:
            print("Alteryx is starting...")

        self.process = subprocess.Popen(
            command, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid
        )
        while True:
            line = self.process.stdout.readline()
            line = (
                line.replace("'", "")
                .replace(",", "")
                .replace("\r", "")
                .replace("\n", "")
            )
            self.check_for_error_and_log_message(line=line)
            line = self.process.stderr.readline()
            line = (
                line.replace("'", "")
                .replace(",", "")
                .replace("\r", "")
                .replace("\n", "")
            )
            if not line:
                if self.verbose is True:
                    print("Alteryx worflow completed")
                break

            self.check_for_error_and_log_message(line=line)
            if self.verbose is True:
                print(line)

    def stop(self) -> None:
        """
        Attempt to gracefully stop the Alteryx Engine subprocess.

        This method first tries to terminate the subprocess and waits for it to exit gracefully.
        If the subprocess has already exited or doesn't respond to the termination signal,
        it attempts a forceful termination using the kill signal.

        If the subprocess is still running after forceful termination, it indicates that
        the subprocess might not be responding or exiting properly.

        Returns:
            None: This method doesn't return any value.

        Raises:
            ProcessLookupError: If the subprocess has already exited when attempting to terminate.
            AlteryxEngineError: If the subprocess is still running after forceful termination.
        """
        if self.process.poll() is not None:
            if self.verbose:
                print("Process has already exited.")
        else:
            self.process.terminate()
            self.process.wait()

            if self.verbose:
                print(f"PID {self.process.pid}: Graceful exit signal sent")

        # Check if the process is still running
        if self.process.poll() is None:
            if self.verbose:
                print(
                    f"PID {self.process.pid}: Process did not respond to termination signal. Attempting forceful exit."
                )
            self.process.kill()

            # Check if the process is still running after forceful termination
            if self.process.poll() is None:
                if self.verbose:
                    print(
                        f"PID {self.process.pid}: Process is still running after forceful termination."
                    )
                raise AlteryxEngineError(
                    "Process is still running after forceful termination."
                )
            else:
                print(f"PID {self.process.pid}: Forceful termination successful")

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
        alteryx_name = os.path.basename(self.path_to_alteryx)
        alteryx_name = alteryx_name.replace(".yxmd", "")
        alteryx_name = f"{alteryx_name}_{self.mode}"

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
            insert_query = f"INSERT INTO {self.log_to['table']} (filename, Created, Message, LoggingLevel) VALUES ('{alteryx_name}', getdate(), '{log_message}', '{logging_level}')"
            conn.execute(insert_query)

    def check_for_error_and_log_message(self, log_message: str) -> None:
        """
        Check a log message for specific error conditions and log it to a SQL database.

        This method examines a log message for specific error conditions and logs them with the appropriate severity
        in a SQL database. If the message contains both 'error' and 'warning' keywords, it's logged as a warning.

        Args:
            log_message (str): The log message to be checked and logged.

        Returns:
            None: This method logs the message to a SQL database and may raise an error, but it does not return a value.
        """
        # Convert the log message to lowercase for case-insensitive checks
        lower_message = log_message.lower()

        # Initialize error message and logging level
        error_message = f"Failure: {log_message}"
        logging_level = "ERROR"

        # Check if the log message contains any error keywords
        if "error" in lower_message:
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
