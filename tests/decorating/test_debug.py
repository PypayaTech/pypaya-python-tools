import pytest
import logging
from pypaya_python_tools.decorating.debug import debug, log, trace


def test_debug(capsys):
    @debug
    def add(a, b):
        return a + b

    result = add(3, 4)
    assert result == 7

    captured = capsys.readouterr()
    assert "Calling add with args: (3, 4) kwargs: {}" in captured.out
    assert "add returned: 7" in captured.out


def test_log(caplog):
    @log(level='DEBUG')
    def divide(a, b):
        return a / b

    with caplog.at_level(logging.DEBUG):
        result = divide(10, 2)

    assert result == 5
    assert "Calling divide with args: (10, 2) kwargs: {}" in caplog.text
    assert "divide returned: 5.0" in caplog.text


def test_trace(capsys):
    @trace
    def recursive_function(n):
        if n <= 1:
            return 1
        return n * recursive_function(n - 1)

    result = recursive_function(3)
    assert result == 6

    captured = capsys.readouterr()
    expected_output = (
        "Entering recursive_function(3,)\n"
        "  Entering recursive_function(2,)\n"
        "    Entering recursive_function(1,)\n"
        "    Exiting recursive_function -> 1\n"
        "  Exiting recursive_function -> 2\n"
        "Exiting recursive_function -> 6\n"
    )
    assert captured.out == expected_output
