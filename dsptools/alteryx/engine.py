from abc import ABC, abstractmethod
from typing import Dict, List, Literal, Union
import os
import subprocess
import multiprocessing
import yaml
from sqlalchemy import create_engine
import warnings
from dsptools.errors.alteryx import (
    AlteryxNotFound,
    NotAnAlteryxError,
    AlteryxEngineError,
    AlteryxLoggerError,
)
from dsptools.utils.notifications import handle_failure, timeout


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
        admins: List[Union[str, None]] = None,
        on_error: Literal["ignore", "warn", "raise"] = "raise",
        verbose: bool = False,
    ) -> bool:
        """
        Initialize a new AlteryxEngine instance.

        Args:
            path_to_alteryx (str): The path to the Alteryx workflow file (.yxmd).It is recommended to use the absolute path to avoid execution errors.
            log_to (Dict[str, str]): A dictionary containing information on where to log the execution results. It should include the keys 'table' and 'connection_string'.
            admins (List[str], optional): A list of admin usernames. Required if 'on_error' is set to 'warn'. Defaults to None.
            on_error (Literal['ignore', 'warn', 'raise'], optional): The action to take on workflow errors. Must be one of 'ignore', 'warn', or 'raise'. Defaults to 'raise'.
            verbose (bool, optional): Whether to enable verbose output. Defaults to False.

        Raises:
            AlteryxNotFound: If the specified Alteryx workflow file does not exist.
            NotAnAlteryxError: If the specified file is not a valid Alteryx workflow.
            AttributeError: If the 'on_error' value, 'admins', or 'log_to' dictionary are invalid.
        """
        # Constructor implementation here
        if not os.path.exists(path_to_alteryx):
            raise AlteryxNotFound("The specified file does not exist")
        if not path_to_alteryx.endswith(".yxmd"):
            raise NotAnAlteryxError(
                "The specified file is not a valid Alteryx workflow"
            )

        if on_error not in ["ignore", "warn", "raise"]:
            raise AttributeError(
                f"on_error must be one of ['ignore','warn','raise'], you specified {on_error}"
            )

        if on_error == "warn" and admins is None:
            raise AttributeError(
                f"At least one admin must be provided if your workflow if on_error = 'warn'"
            )

        if "table" not in log_to.keys() or "connection_string" not in log_to.keys():
            raise AttributeError(
                f"The log_to parameter must be a dict with the following keys: 'table','connection_string'. You provided {', '.join(log_to.keys())}"
            )
        self.path_to_alteryx = path_to_alteryx
        self.log_to = log_to
        self.admins = admins
        self.on_error = on_error
        self.verbose = verbose
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
            try:
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
                    break
                self.check_for_error_and_log_message(line=line)

            except AlteryxEngineError as e:
                self.log_to_sql(
                    log_message="FATAL ERROR - ALTERYX STOPPED", logging_level="ERROR"
                )
                if self.verbose is True:
                    print("FATAL ERROR - ALTERYX STOPPING")
                self.stop()
                return False
            except multiprocessing.TimeoutError as e:
                self.log_to_sql(
                    log_message="TIMEOUT ERROR - ALTERYX STOPPED", logging_level="ERROR"
                )
                if self.verbose is True:
                    print("TIMEOUT ERROR - ALTERYX STOPPING")
                self.stop()
                return False
        return True

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

        Example:
            engine = AlteryxEngine(...)
            engine.run()  # Start the subprocess
            # ... (do some work)
            engine.stop()  # Stop the subprocess gracefully or forcefully.
        """
        try:
            self.process.terminate()
            self.process.wait()  # Wait for the process to exit

            if self.verbose:
                print("Process exited gracefully.")
        except ProcessLookupError:
            if self.verbose:
                print("Process has already exited.")
        except:
            if self.verbose:
                print(
                    "Process did not respond to termination signal. Attempting forceful exit."
                )
            self.process.kill()

            # Check if the process is still running
            try:
                self.process.wait(timeout=1)  # Wait for the process to exit
            except subprocess.TimeoutExpired as e:
                if self.verbose:
                    print("Process is still running after forceful termination.")
                    raise e from e

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
                    f"Log table '{self.log_to['table']}' does not exist so it will be created",
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

    def check_for_error_and_log_message(self, line: str) -> None:
        """
        Check a log message for specific error conditions and log it to a SQL database.

        This method examines a log message to identify specific error conditions and logs them with the appropriate severity
        in a SQL database.

        Args:
            line (str): The log message to be checked and logged.

        Returns:
            None: This method logs the message to a SQL database and does not return a value.
        """
        # Define the keywords associated with error conditions
        error_keywords = [
            "Blocking",
            "Unable to translate Alias",
            "Error opening the file",
            "Error",
        ]

        # Convert the log message to lowercase for case-insensitive checks
        lower_line = line.lower()

        # Initialize error message and logging level
        error_message = f"Failure: {line}"
        logging_level = "ERROR"

        # Check if the log message contains any error keywords
        if any(keyword.lower() in lower_line for keyword in error_keywords):
            if self.on_error == "raise":
                raise AlteryxEngineError(
                    f"Exit raised by the following error: {error_message}"
                )
        elif "Warning".lower() in lower_line:
            logging_level = "WARNING"

        # Log the message based on the determined logging level
        self.log_to_sql(
            log_message=error_message if logging_level == "ERROR" else line,
            logging_level=logging_level,
        )


def run_alteryx_from_config(config_path: str) -> None:
    """
    Run an Alteryx workflow based on configuration provided in a YAML file.

    This function reads a YAML configuration file to determine how to run an Alteryx workflow.
    It initializes an `AlteryxEngine` instance with the specified configuration, including the path
    to the Alteryx workflow, logging settings, and error handling. It then decorates the execution of
    the workflow using the `@handle_failure` and `@timeout` decorators, which add error handling and
    timeout functionality. The decorated workflow is executed within this function.

    Args:
        config_path (str): The path to the YAML configuration file.

    Raises:
        ValueError: If the provided configuration file is not a YAML file.

    Example YAML Configuration File:
    ```yaml
    path_to_alteryx: /path/to/your/workflow.yxmd
    log_to:
      table: log_table
      connection_string: your_connection_string
    admins:
      - admin1
      - admin2
    on_error: warn
    verbose: true
    timeout_settings:
      timeout_duration_seconds: 3600
      on_timeout: warn
    ```

    Example Usage:
    ```python
    run_alteryx_from_config("config.yaml")
    ```

    Args:
        config_path (str): The path to the YAML configuration file.

    Returns:
        None

    """
    if not config_path.endswith(".yml") and not config_path.endswith(".yaml"):
        raise ValueError("This function only supports yaml configuration files")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    print(config)
    path_to_alteryx = config["path_to_alteryx"]
    log_to = {
        "table": config["log_to"]["table"],
        "connection_string": config["log_to"]["connection_string"],
    }
    admins = config["admins"]
    verbose = config["verbose"]
    on_error = config["on_error"]
    max_timeout = config["timeout_settings"]["timeout_duration_seconds"]
    on_timeout = config["timeout_settings"]["on_timeout"]
    alteryx_flow = AlteryxEngine(
        path_to_alteryx=path_to_alteryx,
        log_to=log_to,
        admins=admins,
        verbose=verbose,
        on_error=on_error,
    )

    @handle_failure(
        handle=[
            AlteryxEngineError,
            multiprocessing.TimeoutError,
            subprocess.TimeoutExpired,
        ],
        on_error=on_error,
        emails=admins,
    )
    @timeout(
        max_timeout,
        on_timeout=on_timeout,
        emails=admins,
        subject=f"{os.path.basename(path_to_alteryx)} TIMEOUT",
        message=f"{os.path.basename(path_to_alteryx)} timed out after {max_timeout/60} minutes",
    )
    def run_wrapper(alteryx: AlteryxEngine) -> None:
        alteryx.run()

    run_wrapper(alteryx=alteryx_flow)
