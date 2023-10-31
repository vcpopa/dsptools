Module dsptools.utils.execution
===============================

Functions
---------

    
`conditional_polling(executable: Callable[..., Any], condition: Callable[[Any], bool], max_duration: int, interval: int = 60, *args: Any, **kwargs: Any)`
:   Run a function in a loop until a condition is met or a specified amount of time has passed.
    
    Args:
        executable (Callable): The function to be executed in a loop.
        condition (Callable): The condition function that checks if the loop should exit.
        max_duration (int): The maximum duration (in seconds) for which the loop should run.
        interval (int, optional): The time interval (in seconds) between each execution of `function`.
        *args: Positional arguments to be passed to the `function`.
        **kwargs: Keyword arguments to be passed to the `function`.
    
    Returns:
        None
    
    Raises:
        PollingTimeoutError: If the maximum duration is exceeded.
        PollingExecutableError: If an error occurs during function execution.
        PollingConditionError: If an error occurs in the condition function.
    
    Example:
        def custom_function(param):
            # Your custom logic here
            return result
    
        def custom_condition(result):
            return result >= 10
    
        conditional_polling(custom_function, custom_condition, max_duration=3600, interval=300, param="some_value")

    
`handle_failure(handle: Optional[List[Union[Exception, BaseException]]], on_error: Literal['skip', 'warn', 'raise'] = 'warn', enabled: bool = True, *args, **kwargs)`
:   A decorator to send an email notification when specific exceptions occur within a function.
    
    This decorator allows you to specify a list of exception types that, when raised within
    the decorated function, trigger an email notification. The decorator wraps the original
    function and sends an email with the specified parameters if any of the specified exceptions
    are raised.
    
    Args:
        handle (Union[List[Union[Exception, BaseException]], None]): A list of exception types to email on, or None to handle any exception.
        on_error (Literal['skip', 'warn', 'raise']): The action to take when an exception occurs.
        enabled (bool): Whether the decorator is enabled or not.
        *args: Positional arguments to be passed to the `send_email` function.
        **kwargs: Keyword arguments to be passed to the `send_email` function.
    
    Returns:
        Callable: The decorated function.
    
    Example:
        @handle_failure([ValueError, FileNotFoundError], on_error='warn', enabled=True, ["recipient@example.com"], subject="Function Failed", message="An error occurred.")
        def my_function():
            # Your function logic here
            raise ValueError("This is an example error")
    
    The example above will send an email if a `ValueError` or `FileNotFoundError` is raised within `my_function, as long as the `enabled` parameter is set to True.
    
    :param handle: List of exception types to handle, or None to handle any exception
    :param on_error: Action to take when an exception occurs ('skip', 'warn', 'raise')
    :param enabled: Whether the decorator is enabled or not
    :param *args: Additional positional arguments for the `send_email` function
    :param **kwargs: Additional keyword arguments for the `send_email` function

    
`parallelize_execution(function: Callable[..., Any], *args: Any, max_workers: int = 4, executor_type: Literal['thread', 'process'] = 'thread') ‑> List[Any]`
:   Parallelize the execution of a function on input data using ThreadPoolExecutor or ProcessPoolExecutor.
    
    Args:
        function (Callable): The function to be executed in parallel.
        *args (Iterable): Iterable input data to be processed by the function.
        max_workers (int, optional): The maximum number of workers for parallel execution (default is 4).
        executor_type (str, optional): 'thread' for ThreadPoolExecutor or 'process' for ProcessPoolExecutor (default is 'thread').
    
    Returns:
        List: A list of results from the function executions.

    
`retry(max_retries: int, retry_interval: int, enabled: bool = True)`
:   Decorator that retries the decorated function a specified number of times with a given interval.
    
    Args:
        max_retries (int): The maximum number of retries.
        retry_interval (int): The interval in seconds between retries.
        enabled (bool, optional): Whether the decorator is enabled or not. If disabled, the function will execute without retries. Defaults to True.
    
    Returns:
        Callable: The decorated function.
    
    Example:
        @retry(max_retries=3, retry_interval=5, enabled=True)
        def my_function():
            # Your function logic here
            if some_condition:
                raise Exception("Temporary failure")
    
        The example above will retry `my_function` up to 3 times with a 5-second interval between each retry if it raises an exception, as long as the `enabled` parameter is set to True.

    
`timeout(max_timeout: int, on_timeout: Literal['skip', 'warn', 'raise'] = 'warn', enabled: bool = True, *args, **kwargs)`
:   Timeout decorator for limiting the execution time of a function.
    
    This decorator allows you to set a maximum execution time for a function. If the function
    execution time exceeds the specified timeout, the decorator can take action based on the
    `on_timeout` parameter, which can be set to 'skip', 'warn', or 'raise'. By default, it warns
    when a timeout occurs.
    
    Args:
        max_timeout (int): The maximum execution time allowed for the decorated function, in seconds.
        on_timeout (Literal['skip', 'warn', 'raise'], optional): The action to take when a timeout occurs.
            'skip' will continue executing the function, 'warn' will display a warning message, and 'raise'
            will raise a `multiprocessing.TimeoutError`. Defaults to 'warn'.
        enabled (bool, optional): Whether the decorator is enabled or not. If disabled, the function will execute without timeout control. Defaults to True.
        *args: Additional positional arguments to be passed to the email sending function when a timeout occurs.
        **kwargs: Additional keyword arguments to be passed to the email sending function when a timeout occurs.
    
    Returns:
        Callable: The decorated function.
    
    Example Usage:
    ```python
    @timeout(max_timeout=60, on_timeout='warn', enabled=True, emails=['admin@example.com'], subject='Function Timeout', message='Function execution time exceeded')
    def my_function():
        # Function logic here
    ```
    
    Args:
        max_timeout (int): The maximum execution time allowed for the decorated function, in seconds.
        on_timeout (Literal['skip', 'warn', 'raise'], optional): The action to take when a timeout occurs.
        enabled (bool, optional): Whether the decorator is enabled or not.
        *args: Additional positional arguments for the email sending function.
        **kwargs: Additional keyword arguments for the email sending function.
    
    Returns:
        Callable: The decorated function.

Classes
-------

`RetryTimeout(*args, **kwargs)`
:   Common base class for all non-exit exceptions.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException