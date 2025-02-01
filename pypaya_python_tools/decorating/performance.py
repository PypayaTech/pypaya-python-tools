import functools
import time
from typing import Any, Callable, TypeVar, Dict


T = TypeVar('T')


def memoize(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that caches the results of a function.

    Args:
        func (Callable[..., T]): The function to be memoized.

    Returns:
        Callable[..., T]: The memoized function.

    Example:
        >>> @memoize
        ... def fibonacci(n):
        ...     if n < 2:
        ...         return n
        ...     return fibonacci(n-1) + fibonacci(n-2)
        >>> fibonacci(100)  # This will be much faster than without memoization
    """
    cache: Dict[str, Any] = {}

    @functools.wraps(func)
    def memoized(*args: Any, **kwargs: Any) -> T:
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    return memoized


def timer(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that measures the execution time of a function.

    Args:
        func (Callable[..., T]): The function to be timed.

    Returns:
        Callable[..., T]: The timed function.

    Example:
        >>> @timer
        ... def slow_function():
        ...     time.sleep(2)
        >>> slow_function()
        Execution time: 2.00123 seconds
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Execution time of {func.__name__}: {end_time - start_time:.5f} seconds")
        return result
    return wrapper


def profile(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that profiles the execution of a function, including call count and total time.

    Args:
        func (Callable[..., T]): The function to be profiled.

    Returns:
        Callable[..., T]: The profiled function.

    Example:
        >>> @profile
        ... def test_function(x):
        ...     return x * 2
        >>> for i in range(5):
        ...     test_function(i)
        >>> print_profile_stats()
        Function 'test_function' called 5 times. Total execution time: X.XXXXX seconds.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        wrapper.call_count += 1
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        wrapper.total_time += end_time - start_time
        return result

    wrapper.call_count = 0
    wrapper.total_time = 0
    return wrapper


def print_profile_stats() -> None:
    """
    Prints profiling statistics for all functions decorated with @profile.

    This function should be called after executing the profiled functions to see the results.
    """
    for name, func in globals().items():
        if hasattr(func, 'call_count') and hasattr(func, 'total_time'):
            print(f"Function '{name}' called {func.call_count} times. "
                  f"Total execution time: {func.total_time:.5f} seconds.")
