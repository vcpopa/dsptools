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

    
`parallelize_execution(function: Callable[..., Any], *args: Any, max_workers: int = 4, executor_type: Literal['thread', 'process'] = 'thread') ‑> List[Any]`
:   Parallelize the execution of a function on input data using ThreadPoolExecutor or ProcessPoolExecutor.
    
    Args:
        function (Callable): The function to be executed in parallel.
        *args (Iterable): Iterable input data to be processed by the function.
        max_workers (int, optional): The maximum number of workers for parallel execution (default is 4).
        executor_type (str, optional): 'thread' for ThreadPoolExecutor or 'process' for ProcessPoolExecutor (default is 'thread').
    
    Returns:
        List: A list of results from the function executions.

    
`retry(max_retries: int, retry_interval: int)`
:   Decorator that retries the decorated function a specified number of times with a given interval.
    
    Args:
        max_retries (int): The maximum number of retries.
        retry_interval (int): The interval in seconds between retries.
    
    Returns:
        Callable: The decorated function.
    
    Example:
        @retry(max_retries=3, retry_interval=5)
        def my_function():
            # Your function logic here
            if some_condition:
                raise Exception("Temporary failure")
    
        The example above will retry `my_function` up to 3 times with a 5-second interval between each retry if it raises an exception.