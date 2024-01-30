# pylint: disable = keyword-arg-before-vararg
from __future__ import annotations
import time
from typing import Callable, Any, Union, List, Literal
from functools import wraps
import multiprocessing
import multiprocessing.pool as mppool
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dsptools.errors.execution import (
    PollingConditionError,
    PollingExecutableError,
    PollingTimeoutError,
    RetryTimeout,
)
from dsptools.utils.notifications import send_email


def conditional_polling(
    executable: Callable[..., Any],
    condition: Callable[[Any], bool],
    max_duration: int,
    interval: int = 60,
    *args: Any,
    **kwargs: Any,
):
    """
    Run a function in a loop until a condition is met or a specified amount of time has passed.

    Args:
        executable (Callable): The function to be executed in a loop.
        condition (Callable): The condition function that checks if the loop should exit.
        max_duration (int): The maximum duration (in seconds) for which the loop should run.
        interval (int, optional): The time interval (in seconds) between each execution of `function`.
        *args: Positional arguments to be passed to the `function`.
        **kwargs: Keyword arguments to be passed to the `function`.

    Raises:
        PollingTimeoutError: If the maximum duration is exceeded.
        PollingExecutableError: If an error occurs during function execution.
        PollingConditionError: If an error occurs in the condition function.
        ValueError: If params don't match constrains

    Example:
        def custom_function(param):
            # Your custom logic here
            return result

        def custom_condition(result):
            return result >= 10

        conditional_polling(custom_function, custom_condition, max_duration=3600, interval=300, param="some_value")
    """
    if max_duration <= 0 or interval <= 0:
        raise ValueError("Duration and interval value must be positive")

    if max_duration < interval:
        raise ValueError("Polling interval cannot exceed maximum timeout")

    start_time = time.time()
    while True:
        try:
            result = executable(*args, **kwargs)
        except Exception as e:
            raise PollingExecutableError(
                f"An error occurred during function execution: {str(e)}"
            ) from e

        try:
            if condition(result):
                return result
        except Exception as e:
            raise PollingConditionError(
                f"An error occurred in the condition function: {str(e)}"
            ) from e

        if (time.time() - start_time) >= max_duration:
            raise PollingTimeoutError("Max duration exceeded")

        time.sleep(interval)


def parallelize_execution(
    function: Callable[..., Any],
    *args: Any,
    max_workers: int = 4,
    executor_type: Literal["thread", "process"] = "thread",
) -> List[Any]:
    """
    Parallelize the execution of a function on input data using ThreadPoolExecutor or ProcessPoolExecutor.

    Args:
        function (Callable): The function to be executed in parallel.
        *args (Iterable): Iterable input data to be processed by the function.
        max_workers (int, optional): The maximum number of workers for parallel execution (default is 4).
        executor_type (str, optional): 'thread' for ThreadPoolExecutor or 'process' for ProcessPoolExecutor (default is 'thread').

    Returns:
        List: A list of results from the function executions.
    """
    if executor_type == "thread":
        executor = ThreadPoolExecutor(max_workers=max_workers)
    elif executor_type == "process":
        executor = ProcessPoolExecutor(max_workers=max_workers)  # type: ignore[assignment]
    else:
        raise ValueError("Invalid executor_type. Use 'thread' or 'process'.")

    try:
        results = list(executor.map(function, *args))
    finally:
        executor.shutdown()

    return results


def retry(max_retries: int, retry_interval: int, enabled: bool = True):
    """
    Decorator that retries the decorated function a specified number of times with a given interval.

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
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            if enabled:
                retries = 0
                while retries < max_retries:
                    try:
                        return func(*args, **kwargs)
                    except Exception:
                        retries += 1
                        if retries < max_retries:
                            time.sleep(retry_interval)
                raise RetryTimeout(f"Max retries ({max_retries}) exceeded")

            return func(
                *args, **kwargs
            )  # Decorator is disabled, execute the original function

        return wrapper

    return decorator


def handle_failure(
    handle: Union[List[Union[Exception, BaseException]], None],
    on_error: Literal["skip", "warn", "raise"] = "warn",
    enabled: bool = True,
    *args,
    **kwargs,
):
    """
    A decorator to send an email notification when specific exceptions occur within a function.

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
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*func_args, **func_kwargs):
            if enabled:
                try:
                    print(f"Decorator triggered with {on_error}")
                    print(f"Sending to {func_args}")
                    print(*func_args)
                    return func(*func_args, **func_kwargs)
                except Exception as e:
                    if handle is None or any(
                        isinstance(e, exception_type) for exception_type in handle
                    ):
                        if on_error == "warn":
                            send_email(
                                message=f"Error in {func.__name__}: {str(e)}\n This is a warning, this error has been caught and skipped",
                                *args,
                                **kwargs,
                            )
                        elif on_error == "raise":
                            send_email(
                                message=f"Error in {func.__name__}: {str(e)}\n This error raised an exit",
                                *args,
                                **kwargs,
                            )
                            raise e  # Re-raise the exception after sending the email
                        else:
                            print(
                                f"Decorator set to {on_error}. The following error was caught and handled:\n{str(e)}"
                            )
                    else:
                        raise e  # Re-raise the exception if it's not in the list of exceptions to handle
            else:
                return func(
                    *func_args, **func_kwargs
                )  # Decorator is disabled, just call the original function

        return wrapper

    return decorator


def timeout(
    max_timeout: int,
    on_timeout: Literal["skip", "warn", "raise"] = "warn",
    enabled: bool = True,  # New parameter to enable/disable the decorator
    *args,
    **kwargs,
):
    """
    Timeout decorator for limiting the execution time of a function.

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
    """

    def timeout_decorator(item):
        """Wrap the original function."""

        @wraps(item)
        def func_wrapper(*args, **kwargs):
            """Closure for function."""
            if enabled:
                pool = mppool.ThreadPool(processes=1)
                async_result = pool.apply_async(item, args, kwargs)

                try:
                    # Get the result within the specified timeout
                    result = async_result.get(max_timeout)
                    return result
                except multiprocessing.TimeoutError as e:
                    if on_timeout == "warn":
                        send_email(
                            *args,
                            **kwargs,
                        )
                    elif on_timeout == "raise":
                        send_email(
                            *args,
                            **kwargs,
                        )
                        raise e  # Re-raise the exception after sending the email
                    else:
                        print(
                            f"Decorator set to {on_timeout}. The following error was caught and handled:\n{str(e)}"
                        )

                # Allow the decorated function to continue running even after timeout
                return (
                    None  # You may choose to return a default value or None on timeout
                )
            return item(
                *args, **kwargs
            )  # Decorator is disabled, execute the original function

        return func_wrapper

    return timeout_decorator
