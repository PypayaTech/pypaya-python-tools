import pytest
import time
import threading
from pypaya_python_tools.decorating.behavior import singleton, synchronized, rate_limit, lazy_property


def test_singleton():
    @singleton
    class TestClass:
        def __init__(self):
            self.value = 42

    instance1 = TestClass()
    instance2 = TestClass()

    assert instance1 is instance2
    assert instance1.value == 42

    instance1.value = 100
    assert instance2.value == 100


def test_synchronized():
    counter = 0

    @synchronized()
    def increment():
        nonlocal counter
        current = counter
        time.sleep(0.01)  # Simulate some work
        counter = current + 1

    threads = [threading.Thread(target=increment) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert counter == 10


def test_rate_limit():
    call_times = []

    @rate_limit(calls=3, period=1)
    def limited_function():
        call_times.append(time.time())

    start_time = time.time()
    for _ in range(5):
        limited_function()
    end_time = time.time()

    assert len(call_times) == 5
    assert call_times[-1] - call_times[0] >= 1  # At least 1 second between first and last call
    assert end_time - start_time >= 1  # Total execution time should be at least 1 second


class TestLazyProperty:
    def test_lazy_property(self):
        class ExpensiveObject:
            def __init__(self):
                self.compute_count = 0

            @lazy_property
            def expensive_value(self):
                self.compute_count += 1
                return sum(range(1000000))

        obj = ExpensiveObject()
        assert obj.compute_count == 0

        value1 = obj.expensive_value
        assert obj.compute_count == 1

        value2 = obj.expensive_value
        assert obj.compute_count == 1  # Should not recompute
        assert value1 == value2
