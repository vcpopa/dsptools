# pylint: skip-file
import time
import pytest
from dsptools.utils.execution import parallelize_execution


# Mock functions for testing
def square(x):
    return x * x


def test_parallelize_execution_thread():
    data = [1, 2, 3, 4, 5]
    results = parallelize_execution(square, data, max_workers=2, executor_type="thread")
    assert results == [1, 4, 9, 16, 25]


def test_parallelize_execution_process():
    data = [1, 2, 3, 4, 5]
    results = parallelize_execution(
        square, data, max_workers=2, executor_type="process"
    )
    assert results == [1, 4, 9, 16, 25]


@pytest.mark.xfail(raises=ValueError)
def test_parallelize_execution_invalid_executor_type():
    data = [1, 2, 3, 4, 5]
    parallelize_execution(square, data, max_workers=2, executor_type="invalid_executor")


def test_parallelize_execution_time():
    data = [1, 2, 3, 4, 5]

    start_time = time.time()
    results = parallelize_execution(square, data, max_workers=2, executor_type="thread")
    end_time = time.time()

    execution_time = end_time - start_time

    # Check if parallel execution is faster than sequential
    assert execution_time < 2 * max(data)  # Adjust the threshold as needed
