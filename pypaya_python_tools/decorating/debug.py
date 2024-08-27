import functools
import logging
from typing import Any, Callable, TypeVar


T = TypeVar('T')


def debug(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that prints debug information about the function call and its result.

    Args:
        func (Callable[..., T]): The function to be debugged.

    Returns:
        Callable[..., T]: The debugged function.

    Example:
        >>> @debug
        ... def add(a, b):
        ...     return a + b
        >>> add(3, 4)
        Calling add with args: (3, 4) kwargs: {}
        add returned: 7
        7
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        print(f"Calling {func.__name__} with args: {args} kwargs: {kwargs}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned: {result}")
        return result
    return wrapper


def log(level: str = 'INFO') -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that logs function calls and their results.

    Args:
        level (str): The logging level to use. Defaults to 'INFO'.

    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]: A decorator function.

    Example:
        >>> @log(level='DEBUG')
        ... def divide(a, b):
        ...     return a / b
        >>> divide(10, 2)
        # This will log: "DEBUG:root:Calling divide with args: (10, 2) kwargs: {}"
        #                "DEBUG:root:divide returned: 5.0"
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            logger = logging.getLogger(func.__module__)
            logger.setLevel(level)
            logger.debug(f"Calling {func.__name__} with args: {args} kwargs: {kwargs}")
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned: {result}")
            return result
        return wrapper
    return decorator


def trace(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that traces the execution of a function, showing entry and exit points.

    Args:
        func (Callable[..., T]): The function to be traced.

    Returns:
        Callable[..., T]: The traced function.

    Example:
        >>> @trace
        ... def recursive_function(n):
        ...     if n <= 1:
        ...         return 1
        ...     return n * recursive_function(n - 1)
        >>> recursive_function(3)
        Entering recursive_function(3)
          Entering recursive_function(2)
            Entering recursive_function(1)
            Exiting recursive_function -> 1
          Exiting recursive_function -> 2
        Exiting recursive_function -> 6
        6
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        indent = '  ' * wrapper.level
        print(f"{indent}Entering {func.__name__}{args}")
        wrapper.level += 1
        result = func(*args, **kwargs)
        wrapper.level -= 1
        print(f"{indent}Exiting {func.__name__} -> {result}")
        return result
    wrapper.level = 0
    return wrapper
