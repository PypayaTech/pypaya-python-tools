import pytest
from pypaya_python_tools.decorating.error_handling import retry, catch_exceptions, validate_args


def test_retry():
    attempt_count = 0

    @retry(max_attempts=3, delay=0.1, exceptions=ValueError)
    def unstable_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError("Not ready yet")
        return "Success"

    result = unstable_function()
    assert result == "Success"
    assert attempt_count == 3


def test_retry_max_attempts_reached():
    @retry(max_attempts=3, delay=0.1, exceptions=ValueError)
    def always_fails():
        raise ValueError("Always fails")

    with pytest.raises(ValueError, match="Always fails"):
        always_fails()


def test_catch_exceptions():
    def handler(e):
        return f"Caught an exception: {str(e)}"

    @catch_exceptions(handler)
    def risky_function(x):
        return 10 / x

    assert risky_function(2) == 5
    assert risky_function(0) == "Caught an exception: division by zero"


def test_validate_args_single_validator():
    def is_positive(x):
        return x > 0

    @validate_args(x=is_positive)
    def func(x):
        return x * 2

    assert func(5) == 10
    with pytest.raises(ValueError, match="Validation failed for argument 'x'"):
        func(-5)


def test_validate_args_multiple_validators():
    def is_positive(x):
        return x > 0

    def is_even(x):
        return x % 2 == 0

    @validate_args(x=[is_positive, is_even])
    def func(x):
        return x * 2

    assert func(4) == 8
    with pytest.raises(ValueError, match="Validation failed for argument 'x'"):
        func(3)
    with pytest.raises(ValueError, match="Validation failed for argument 'x'"):
        func(-2)


def test_validate_args_multiple_arguments():
    def is_positive(x):
        return x > 0

    def is_string(x):
        return isinstance(x, str)

    @validate_args(x=is_positive, y=is_string)
    def func(x, y):
        return f"{y}: {x * 2}"

    assert func(5, "Result") == "Result: 10"
    with pytest.raises(ValueError, match="Validation failed for argument 'x'"):
        func(-5, "Result")
    with pytest.raises(ValueError, match="Validation failed for argument 'y'"):
        func(5, 123)


def test_validate_args_keyword_arguments():
    def is_positive(x):
        return x > 0

    @validate_args(x=is_positive, y=is_positive)
    def func(x, y):
        return x + y

    assert func(x=5, y=3) == 8
    with pytest.raises(ValueError, match="Validation failed for argument 'y'"):
        func(x=5, y=-3)


def test_validate_args_optional_arguments():
    def is_positive(x):
        return x > 0

    @validate_args(x=is_positive, y=is_positive)
    def func(x, y=10):
        return x + y

    assert func(5) == 15
    assert func(5, 3) == 8
    with pytest.raises(ValueError, match="Validation failed for argument 'y'"):
        func(5, -3)


def test_validate_args_no_validation():
    @validate_args()
    def func(x):
        return x * 2

    assert func(5) == 10
    assert func(-5) == -10  # No validation, so this should work


def test_validate_args_mixed_validators():
    def is_positive(x):
        return x > 0

    def is_even(x):
        return x % 2 == 0

    def is_string(x):
        return isinstance(x, str)

    @validate_args(x=[is_positive, is_even], y=is_string, z=is_positive)
    def func(x, y, z=1):
        return f"{y}: {x * z}"

    assert func(4, "Result", 2) == "Result: 8"
    assert func(4, "Result") == "Result: 4"
    with pytest.raises(ValueError, match="Validation failed for argument 'x'"):
        func(3, "Result")
    with pytest.raises(ValueError, match="Validation failed for argument 'y'"):
        func(4, 123)
    with pytest.raises(ValueError, match="Validation failed for argument 'z'"):
        func(4, "Result", -1)
