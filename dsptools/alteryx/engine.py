from __future__ import annotations
from typing import Dict, Literal, Union
import time
import os
from abc import ABC, abstractmethod
import warnings
import asyncio
import psutil
from sqlalchemy import create_engine, text
from dsptools.errors.alteryx import (
    AlteryxNotFound,
    NotAnAlteryxError,
    AlteryxEngineError,
    AlteryxLoggerError,
    AlteryxKillError,
)


class AlteryxEngineScaffold(ABC):
    @abstractmethod
    async def run(self) -> int:
        pass

    @abstractmethod
    async def stop(self, reason: Literal["killswitch", "error"]) -> None:
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

    async def run(self) -> int:
        """
        Start and run the Alteryx workflow asynchronously.

        Starts the Alteryx process, monitors its output, and logs messages.

        """
        command = rf'"C:\Program Files\Alteryx\bin\AlteryxEngineCmd.exe" "{self.path_to_alteryx}"'
        if self.verbose:
            print("Alteryx is starting...")

        self.create_log_table_if_not_exist()

        # Start the Alteryx process asynchronously
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self.parent_pid = process.pid
        print(f"Parent PID: {self.parent_pid}")

        # Start the task to retrieve the child PID with a timeout
        try:
            self.child_pid = await asyncio.wait_for(
                self.get_child_pid_async(self.parent_pid), timeout=120
            )
        except asyncio.TimeoutError as exc:
            # Terminate the parent process if the child PID was not obtained within the specified time
            process.terminate()
            raise AlteryxEngineError(
                "Child PID not obtained within the specified time."
            ) from exc

        if self.child_pid is None:
            raise AlteryxEngineError("Child PID not found.")

        # Process stdout and stderr asynchronously
        async def process_output(stream_name, stream):
            async for line in stream:
                line = line.decode("utf-8")
                line = self.clean_line(line)
                print(line)
                await self.check_for_error_and_log_message(log_message=line)
                if self.verbose:
                    print(f"{stream_name}: {line}")

        # Wait for the Alteryx process to complete
        await asyncio.gather(
            process_output("stdout", process.stdout),
            process_output("stderr", process.stderr),
        )

        returncode = await process.wait()

        if self.verbose:
            print("Alteryx workflow completed")
        return returncode

    async def get_child_pid_async(self, parent_pid: int) -> Union[int, None]:
        """
        Find the child PID of a given parent process within a specified timeout period.

        Args:
            parent_pid (int): The parent process ID to search for child processes.

        Returns:
            Union[int, None]: The process ID of a child process, or None if no child process is found within the timeout.
        """
        start_time = time.time()

        while True:
            try:
                # Obtain information about the parent process
                proc = psutil.Process(parent_pid)
                children = proc.children()
                print(f"Children: {children}")
                if children != []:
                    return children[0].pid
                if (time.time() - start_time) >= 120:
                    raise asyncio.TimeoutError(
                        "Child PID not obtained within the specified time"
                    )
                # Poll every 3 seconds
                await asyncio.sleep(3)
            except (psutil.NoSuchProcess, IndexError) as exc:
                raise AlteryxEngineError("Parent PID does not exist") from exc

    def clean_line(self, line: str) -> str:
        """
        Clean a line by removing unwanted characters.
        """
        return (
            line.replace("'", "").replace(",", "").replace("\r", "").replace("\n", "")
        )

    async def stop(self, reason: Literal["killswitch", "error"]) -> None:
        """
        Stop the Alteryx workflow and kill associated processes asynchronously.

        Terminates the Alteryx process and its child processes.

        Raises:
            AlteryxKillError: If any of the processes could not be killed.
            AlteryxEngineError: If parent and/or child PIDs not found.

        """
        # Start tasks to kill both parent and child processes asynchronously
        if self.parent_pid and self.child_pid:
            parent_kill_task = asyncio.create_task(self.kill_pid_async(self.parent_pid))
            child_kill_task = asyncio.create_task(self.kill_pid_async(self.child_pid))
        else:
            raise AlteryxEngineError(
                "Could not find all required PIDS, process may not have started"
            )

        # Wait for both tasks to complete
        await asyncio.gather(parent_kill_task, child_kill_task)

        # Check if any of the processes could not be killed
        if parent_kill_task.result() is None:
            self.log_to_sql(
                log_message=f"Parent PID {self.parent_pid} could not be killed",
                logging_level="ERROR",
            )
            raise AlteryxKillError(f"Parent PID {self.parent_pid} could not be killed")

        if child_kill_task.result() is None:
            self.log_to_sql(
                log_message=f"Child PID {self.child_pid} could not be killed",
                logging_level="ERROR",
            )
            raise AlteryxKillError(f"Child PID {self.child_pid} could not be killed")

        self.log_to_sql(log_message="ALL PIDS HAVE BEEN KILLED", logging_level="INFO")
        self.log_to_sql(log_message=f"STOP REASON: {reason}", logging_level="INFO")

    async def kill_pid_async(self, pid: int) -> Union[int, None]:
        """
        Terminate a process with the given process ID asynchronously
        and check if it was successfully killed.

        Args:
            pid (int): The process ID to terminate.

        Returns:
            Union[int, None]: The process ID if it was successfully killed, or None if not.
        """
        try:
            pid_process = psutil.Process(pid)
            pid_process.terminate()

            # Wait for the process to exit asynchronously
            await asyncio.to_thread(pid_process.wait, 5)

            # Check if the process exists
            if not psutil.pid_exists(pid):
                return pid

            return None
        except psutil.NoSuchProcess:
            return None

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

        con = create_engine(self.log_to["connection_string"])
        with con.connect() as conn:
            insert_query = text(
                f"INSERT INTO Dataflow.{self.log_to['table']} (filename, Created, Message, LoggingLevel,ParentPID,ChildPID) VALUES ('{self.alteryx_name}', getdate(), '{log_message}', '{logging_level}','{self.parent_pid}','{self.child_pid}')"
            )
            print(f"Executing {insert_query}")
            conn.execute(insert_query)

    def create_log_table_if_not_exist(self) -> None:
        # Extract schema and table from self.log_to['table']
        schema, table = self.log_to["table"].split(".", 1)
        con = create_engine(self.log_to["connection_string"])
        with con.connect() as conn:
            # Check if the schema exists
            schema_exists_query = text(
                f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{schema}'"
            )

            if (conn.execute(schema_exists_query).scalar()) is False:
                raise AlteryxLoggerError(
                    f"Schema '{schema}' does not exist. Cannot create the log table."
                )

            # Check if the table exists
            table_exists_query = text(
                f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'"
            )

            if conn.execute(table_exists_query).scalar() is None:
                warnings.warn(
                    f"Log table '{self.log_to['table']}' was created!",
                    UserWarning,
                )
                # Log table doesn't exist, create it
                create_table_query = text(
                    f"""
                    CREATE TABLE Dataflow.{self.log_to['table']} (
                        filename VARCHAR(255),
                        Created DATETIME,
                        Message VARCHAR(MAX),
                        LoggingLevel VARCHAR(10),
                        ParentPID INT,
                        ChildPID INT
                    )
                """
                )
                conn.execute(create_table_query)

    async def check_for_error_and_log_message(self, log_message: str) -> None:
        """
        Check a log message for specific error conditions and log it to a SQL database.

        This method examines a log message for specific error conditions and logs them with the appropriate severity
        in a SQL database. If the message contains any of the error keywords, it's logged as an error.
        If the message contains any of the warning keywords, it's logged as a warning.

        Args:
            log_message (str): The log message to be checked and logged.

        Raises:
            AlteryxEngineError: If the log message contains any of the specified error keywords.

        """
        # Convert the log message to lowercase for case-insensitive checks
        lower_message = log_message.lower()

        # Initialize error message and logging level
        error_message = f"Failure: {log_message}"

        # Check if the log message contains any error keywords
        error_keywords = [
            "blocking",
            "unable to translate alias",
            "error opening the file",
            "can't find the file",
        ]
        if any(keyword in lower_message for keyword in error_keywords):
            if self.verbose:
                warnings.warn(log_message)
            self.log_to_sql(log_message=error_message, logging_level="ERROR")  # type: ignore[arg-type]
            await self.stop(reason="error")
            raise AlteryxEngineError(
                f"Exit raised by the following error: {error_message}"
            )
        # Check if the log message contains any warning keywords
        warning_keywords = ["warning"]
        if any(keyword in lower_message for keyword in warning_keywords):
            if self.verbose:
                warnings.warn(log_message)
            # Log the message to a SQL database
            self.log_to_sql(log_message=log_message, logging_level="WARNING")
        self.log_to_sql(log_message=log_message, logging_level="INFO")
