# pylint: skip-file
import pytest
import random
from dsptools.utils.execution import (
    conditional_polling,
    PollingTimeoutError,
    PollingExecutableError,
    PollingConditionError,
)


# Mock functions for testing
def mock_successful_function(param):
    return param  # Returns the input parameter


def mock_condition(result):
    if result >= 10:
        return result
    result


def mock_eventual_success(param):
    return param + random.randint(3, 5)


def mock_failure(param):
    return param - 5


def failing_condition(param):
    raise ValueError("This is meant to happen")


def test_conditional_polling_first_time_success():
    # Test when the condition succeeds after some iterations
    result = conditional_polling(
        executable=mock_successful_function,
        condition=mock_condition,
        max_duration=10,
        interval=1,
        param=10,
    )
    assert result == 10


def test_conditional_polling_condition_eventual_success():
    # Test when the condition succeeds after some iterations
    result = conditional_polling(
        executable=mock_eventual_success,
        condition=mock_condition,
        max_duration=10,
        interval=1,
        param=5,
    )
    assert result == 10


@pytest.mark.xfail(raises=PollingTimeoutError, strict=True)
def test_conditional_polling_timeout():
    # Test when the condition succeeds after some iterations
    result = conditional_polling(
        executable=mock_failure,
        condition=mock_condition,
        max_duration=10,
        interval=1,
        param=5,
    )
    assert result == 10


@pytest.mark.xfail(raises=PollingExecutableError, strict=True)
def test_conditional_polling_no_executable():
    # Test when no executable function is provided
    with pytest.raises(ValueError):
        conditional_polling(
            executable=None,
            condition=mock_condition,
            max_duration=10,
            interval=1,
            param=5,
        )


@pytest.mark.xfail(raises=PollingConditionError, strict=True)
def test_conditional_polling_no_condition():
    # Test when no condition function is provided
    with pytest.raises(ValueError):
        conditional_polling(
            executable=mock_successful_function,
            condition=None,
            max_duration=10,
            interval=1,
            param=5,
        )


@pytest.mark.xfail(raises=PollingConditionError, strict=True)
def test_conditional_polling_wrong_condition():
    # Test when no condition function is provided
    with pytest.raises(ValueError):
        conditional_polling(
            executable=mock_successful_function,
            condition=failing_condition,
            max_duration=10,
            interval=1,
            param=5,
        )


@pytest.mark.xfail(raises=ValueError, strict=True)
def test_conditional_polling_zero_duration():
    # Test when max duration is set to zero

    conditional_polling(
        executable=mock_successful_function,
        condition=mock_condition,
        max_duration=0,
        interval=1,
        param=5,
    )


@pytest.mark.xfail(raises=ValueError, strict=True)
def test_conditional_polling_interval_bigger_than_maxtimeout():
    # Test when the interval is set to a negative value

    conditional_polling(
        executable=mock_successful_function,
        condition=mock_condition,
        max_duration=5,
        interval=10,
        param=5,
    )
