import pytest
import time
from pypaya_python_tools.decorating.performance import memoize, timer, profile


def test_memoize():
    call_count = 0

    @memoize
    def fibonacci(n):
        nonlocal call_count
        call_count += 1
        if n < 2:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)

    assert fibonacci(10) == 55
    assert call_count == 11  # Function should be called 11 times for fibonacci(10)

    call_count = 0
    assert fibonacci(10) == 55
    assert call_count == 0  # Function should not be called again due to memoization


def test_timer(capsys):
    @timer
    def slow_function():
        time.sleep(0.1)

    slow_function()

    captured = capsys.readouterr()
    assert "Execution time of slow_function:" in captured.out
    assert "seconds" in captured.out


def test_profile():
    @profile
    def test_function(x):
        time.sleep(0.01)  # Add a small delay to make timing more reliable
        return x * 2

    for i in range(5):
        assert test_function(i) == i * 2

    assert hasattr(test_function, 'call_count')
    assert hasattr(test_function, 'total_time')
    assert test_function.call_count == 5
    assert test_function.total_time >= 0.05  # Should be at least 0.05 seconds (5 * 0.01)
