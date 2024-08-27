import functools
import inspect
import time
from typing import Any, Callable, TypeVar, Union, Type, List

T = TypeVar('T')


def retry(max_attempts: int = 3, delay: float = 1.0,
          exceptions: Union[Type[Exception], tuple] = Exception) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that retries a function a specified number of times with a delay.

    Args:
        max_attempts (int): Maximum number of attempts to retry the function. Defaults to 3.
        delay (float): Delay in seconds between retries. Defaults to 1.0.
        exceptions (Union[Type[Exception], tuple]): Exception or tuple of exceptions to catch. Defaults to Exception.

    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]: A decorator function.

    Example:
        >>> @retry(max_attempts=5, delay=2, exceptions=(ValueError, TypeError))
        ... def unstable_function():
        ...     import random
        ...     if random.random() < 0.8:
        ...         raise ValueError("Random error")
        ...     return "Success"
        >>> unstable_function()
        # This will retry up to 5 times if ValueError or TypeError is raised
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise e
                    time.sleep(delay)
            return None  # This line should never be reached
        return wrapper
    return decorator


def catch_exceptions(exception_handler: Callable[[Exception], Any]) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that catches exceptions and handles them with a provided exception handler function.

    Args:
        exception_handler (Callable[[Exception], Any]): A function that takes an exception as input and handles it.

    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]: A decorator function.

    Example:
        >>> def handle_exception(e):
        ...     print(f"An error occurred: {e}")
        ...     return None
        >>> @catch_exceptions(handle_exception)
        ... def risky_function(x):
        ...     return 10 / x
        >>> risky_function(0)
        An error occurred: division by zero
        None
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return exception_handler(e)
        return wrapper
    return decorator


ValidatorType = Callable[[Any], bool]
ValidatorSpec = Union[ValidatorType, List[ValidatorType]]


def validate_args(**validator_dict: ValidatorSpec) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    A flexible decorator for validating function arguments.

    Args:
        **validator_dict: A dictionary where keys are parameter names and values are either
                          a single validator function or a list of validator functions.

    Returns:
        A decorator function.

    Example:
        >>> def is_positive(x):
        ...     return x > 0
        >>> def is_even(x):
        ...     return x % 2 == 0
        >>> def is_string(x):
        ...     return isinstance(x, str)
        >>> @validate_args(x=[is_positive, is_even], y=is_string)
        ... def process(x, y):
        ...     return f"{y}: {x * 2}"
        >>> process(4, "Result")
        'Result: 8'
        >>> process(-2, "Result")
        Traceback (most recent call last):
        ...
        ValueError: Validation failed for argument 'x'
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)

            for param_name, arg_value in bound_args.arguments.items():
                if param_name in validator_dict:
                    validators = validator_dict[param_name]
                    if not isinstance(validators, list):
                        validators = [validators]

                    if not all(validator(arg_value) for validator in validators):
                        raise ValueError(f"Validation failed for argument '{param_name}'")

            return func(*args, **kwargs)

        return wrapper

    return decorator
