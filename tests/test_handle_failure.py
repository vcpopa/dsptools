# pylint: skip-file
import pytest
from dsptools.utils.execution import handle_failure


# Define a sample function for testing
def sample_function():
    raise ValueError("This is a sample error")


# Test cases for the handle_failure decorator with on_error set to "skip"
def test_handle_failure_skip_enabled():
    # Test with the decorator enabled and on_error set to "skip"
    handle_decorator = handle_failure([ValueError], on_error="skip", enabled=True)
    decorated_function = handle_decorator(sample_function)

    # The decorated function should not raise an exception
    result = decorated_function()
    assert result is None  # The decorator should continue execution


@pytest.mark.xfail(raises=ValueError, strict=True)
def test_handle_failure_skip_disabled():
    # Test with the decorator disabled and on_error set to "skip"
    handle_decorator = handle_failure([ValueError], on_error="skip", enabled=False)
    decorated_function = handle_decorator(sample_function)
    decorated_function()
