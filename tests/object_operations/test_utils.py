import pytest
from pypaya_python_tools.object_operations.utils import (
    direct,
    get_attribute, set_attribute, del_attribute,
    call, instantiate,
    get_item, set_item, del_item,
    iterate
)
from pypaya_python_tools.object_operations.exceptions import (
    ObjectAttributeError,
    CallError,
    ItemAccessError
)


class TestObject:
    def __init__(self):
        self.value = 42
        self.items = {"a": 1, "b": 2}

    def method(self, x):
        return x * 2


def test_direct_access():
    obj = TestObject()
    result = direct(obj)
    assert result == obj


def test_attribute_operations():
    obj = TestObject()

    # Get
    assert get_attribute(obj, "value") == 42
    assert get_attribute(obj, "nonexistent", default=10) == 10

    # Set
    set_attribute(obj, "value", 100)
    assert obj.value == 100

    # Delete
    del_attribute(obj, "value")
    with pytest.raises(ObjectAttributeError):
        get_attribute(obj, "value")


def test_call_operations():
    obj = TestObject()

    # Method call
    assert call(obj.method, 5) == 10

    # Function call
    def test_func(x, y=1):
        return x + y

    assert call(test_func, 5, y=2) == 7


def test_instantiation():
    class TestClass:
        def __init__(self, value):
            self.value = value

    obj = instantiate(TestClass, 42)
    assert obj.value == 42


def test_container_operations():
    obj = TestObject()

    # Get
    assert get_item(obj.items, "a") == 1

    # Set
    set_item(obj.items, "c", 3)
    assert obj.items["c"] == 3

    # Delete
    del_item(obj.items, "c")
    assert "c" not in obj.items


def test_iteration():
    items = [1, 2, 3]
    iterator = iterate(items)
    assert list(iterator) == items


def test_error_handling():
    obj = TestObject()

    with pytest.raises(ObjectAttributeError):
        get_attribute(obj, "nonexistent")

    with pytest.raises(CallError):
        call(obj.method)  # Missing required argument

    with pytest.raises(ItemAccessError):
        get_item(obj.items, "nonexistent")
