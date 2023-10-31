# pylint: skip-file
import pytest
from dsptools.utils.execution import timeout
import multiprocessing


# Define a sample function for testing
def sample_function():
    # Simulate a function that takes some time to execute
    import time

    time.sleep(2)


# Test cases for the timeout decorator with on_timeout set to "skip"
def test_timeout_skip_enabled():
    # Test with the decorator enabled and on_timeout set to "skip"
    timeout_decorator = timeout(max_timeout=1, on_timeout="skip", enabled=True)
    decorated_function = timeout_decorator(sample_function)

    # The decorated function should not raise a TimeoutError
    decorated_function()


def test_timeout_skip_disabled():
    # Test with the decorator disabled and on_timeout set to "skip"
    timeout_decorator = timeout(max_timeout=1, on_timeout="skip", enabled=False)
    decorated_function = timeout_decorator(sample_function)

    # The decorated function should not raise a TimeoutError
    decorated_function()


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_timeout_raise_enabled():
    # Test with the decorator disabled and on_timeout set to "skip"
    timeout_decorator = timeout(max_timeout=1, on_timeout="raise", enabled=True)
    decorated_function = timeout_decorator(sample_function)

    # The decorated function should not raise a TimeoutError
    decorated_function()
