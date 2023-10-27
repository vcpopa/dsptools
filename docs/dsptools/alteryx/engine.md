Module dsptools.alteryx.engine
==============================

Functions
---------

    
`run_alteryx_from_config(config_path: str) ‑> None`
:   Run an Alteryx workflow based on configuration provided in a YAML file.
    
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

Classes
-------

`AlteryxEngine(path_to_alteryx: str, log_to: Dict[str, str], admins: List[Optional[str]] = None, on_error: Literal['ignore', 'warn', 'raise'] = 'raise', verbose: bool = False)`
:   Represents an Alteryx Engine for executing Alteryx workflows.
    
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

    ### Ancestors (in MRO)

    * dsptools.alteryx.engine.AlteryxEngineScaffold
    * abc.ABC

    ### Methods

    `check_for_error_and_log_message(self, line: str) ‑> None`
    :   Check a log message for specific error conditions and log it to a SQL database.
        
        This method examines a log message to identify specific error conditions and logs them with the appropriate severity
        in a SQL database.
        
        Args:
            line (str): The log message to be checked and logged.
        
        Returns:
            None: This method logs the message to a SQL database and does not return a value.

    `log_to_sql(self, log_message: str, logging_level: Literal['INFO', 'WARNING', 'ERROR']) ‑> None`
    :   Log a message to a SQL database with the specified logging level.
        
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

    `run(self)`
    :   Run the Alteryx workflow specified by path_to_alteryx.
        
        This method initiates the execution of the Alteryx workflow specified by 'path_to_alteryx' by calling
        the Alteryx Engine command-line tool. It captures the workflow's execution logs, checks for errors, and logs
        the messages based on the specified logging settings.
        
        Returns:
            None

    `stop(self) ‑> None`
    :   Attempt to gracefully stop the Alteryx Engine subprocess.
        
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

`AlteryxEngineScaffold()`
:   Helper class that provides a standard way to create an ABC using
    inheritance.

    ### Ancestors (in MRO)

    * abc.ABC

    ### Descendants

    * dsptools.alteryx.engine.AlteryxEngine

    ### Methods

    `log_to_sql(self) ‑> None`
    :

    `run(self) ‑> True`
    :

    `stop(self) ‑> bool`
    :