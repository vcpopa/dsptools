# pylint: skip-file
import random
import pytest
from dsptools.utils.execution import retry
from dsptools.errors.execution import RetryTimeout


# Mock functions for testing
def always_fails():
    raise Exception("Always fails")


def eventually_succeeds():
    static_counter = random.randint(1, 3)
    if static_counter < 3:
        raise Exception("Temporary failure")
    return "Success"


@retry(max_retries=3, retry_interval=1)
def decorated_always_fails():
    return always_fails()


@retry(max_retries=6, retry_interval=1)
def decorated_eventually_succeeds():
    return eventually_succeeds()


def test_retry_max_retries_exceeded():
    # Test when max retries are exceeded
    with pytest.raises(RetryTimeout):
        decorated_always_fails()


def test_retry_eventual_success():
    # Test when the decorated function eventually succeeds
    result = decorated_eventually_succeeds()
    assert result == "Success"


def test_retry_no_exception():
    # Test when the decorated function succeeds without exceptions
    @retry(max_retries=3, retry_interval=1)
    def decorated_succeeds_immediately():
        return "Success"

    result = decorated_succeeds_immediately()
    assert result == "Success"
