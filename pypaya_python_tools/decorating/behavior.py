import functools
import threading
import time
from typing import Any, Callable, TypeVar, Optional, List


T = TypeVar('T')


def singleton(cls: type) -> type:
    """
    Decorator that ensures a class has only one instance.

    Args:
        cls (type): The class to be decorated.

    Returns:
        type: The decorated class.

    Example:
        >>> @singleton
        ... class DatabaseConnection:
        ...     def __init__(self):
        ...         print("Initializing database connection")
        >>> conn1 = DatabaseConnection()
        Initializing database connection
        >>> conn2 = DatabaseConnection()
        >>> conn1 is conn2
        True
    """
    instances = {}

    def get_instance(*args: Any, **kwargs: Any) -> Any:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def synchronized(lock: Optional[threading.Lock] = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that synchronizes access to a function using a threading Lock.

    Args:
        lock (Optional[threading.Lock]): A Lock object to use for synchronization. If None, a new Lock is created.

    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]: A decorator function.

    Example:
        >>> counter = 0
        >>> @synchronized()
        ... def increment():
        ...     global counter
        ...     current = counter
        ...     counter = current + 1
        >>> import threading
        >>> threads = [threading.Thread(target=increment) for _ in range(1000)]
        >>> for t in threads: t.start()
        >>> for t in threads: t.join()
        >>> print(counter)
        1000
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        func_lock = lock or threading.Lock()

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with func_lock:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(calls: int, period: float) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that limits the rate at which a function can be called.

    Args:
        calls (int): Number of calls allowed in the given period.
        period (float): Time period in seconds.

    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]: A decorator function.

    Example:
        >>> import time
        >>> @rate_limit(calls=3, period=1)
        ... def limited_function():
        ...     print("Function called")
        >>> for _ in range(5):
        ...     limited_function()
        ...     time.sleep(0.2)
        Function called
        Function called
        Function called
        # The last two calls will be blocked until the 1-second period has passed
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        lock = threading.Lock()
        call_times: List[float] = []
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with lock:
                now = time.time()
                # Remove calls outside the time period
                call_times[:] = [t for t in call_times if now - t < period]
                if len(call_times) >= calls:
                    sleep_time = call_times[0] + period - now
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                        now = time.time()
                call_times.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def lazy_property(func: Callable[[Any], T]) -> property:
    """
    Decorator that creates a lazy-evaluated property.

    The property value is computed on first access and then cached for subsequent accesses.

    Args:
        func (Callable[[Any], T]): The function to be decorated.

    Returns:
        property: A property descriptor that lazily evaluates the decorated function.

    Example:
        >>> class ExpensiveObject:
        ...     @lazy_property
        ...     def expensive_calculation(self):
        ...         print("Performing expensive calculation...")
        ...         return sum(range(1000000))
        >>> obj = ExpensiveObject()
        >>> obj.expensive_calculation
        Performing expensive calculation...
        499999500000
        >>> obj.expensive_calculation  # Second access doesn't recompute
        499999500000
    """
    attr_name = '_lazy_' + func.__name__

    @property
    @functools.wraps(func)
    def wrapper(self: Any) -> T:
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)

    return wrapper
