Module dsptools.alteryx.engine
==============================

Classes
-------

`AlteryxEngine(path_to_alteryx: str, log_to: Dict[str, str], mode: Literal['PRODUCTION', 'TEST', 'RELEASE'], verbose: bool = False)`
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

    ### Ancestors (in MRO)

    * dsptools.alteryx.engine.AlteryxEngineScaffold
    * abc.ABC

    ### Methods

    `check_for_error_and_log_message(self, log_message: str) ‑> None`
    :   Check a log message for specific error conditions and log it to a SQL database.
        
        This method examines a log message for specific error conditions and logs them with the appropriate severity
        in a SQL database. If the message contains both 'error' and 'warning' keywords, it's logged as a warning.
        
        Args:
            log_message (str): The log message to be checked and logged.
        
        Returns:
            None: This method logs the message to a SQL database and may raise an error, but it does not return a value.

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
            AlteryxEngineError: If the subprocess is still running after forceful termination.

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