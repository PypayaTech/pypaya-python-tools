import pytest
from pypaya_python_tools.object_operations.manager import AccessManager
from pypaya_python_tools.object_operations.definitions import Operation, OperationType
from pypaya_python_tools.object_operations.security import OperationSecurity
from pypaya_python_tools.object_operations.exceptions import SecurityError


def test_complete_workflow():
    # Create manager with security
    security = OperationSecurity(
        allow_private_access=False,
        allow_protected_access=True,
        allow_modification=True,
        allow_dynamic_access=True,
        allow_container_modification=True
    )
    manager = AccessManager(security)

    # Test class instantiation
    class TestClass:
        def __init__(self, value):
            self.value = value
            self._protected = "protected"
            self.items = {"a": 1, "b": 2}

        def method(self, x):
            return x * 2

    # Create instance
    instance = manager.access_object(TestClass, Operation(
        OperationType.INSTANTIATE,
        args=(42,)
    ))

    # Get attribute
    value = manager.access_object(instance, Operation(
        OperationType.GET_ATTRIBUTE,
        args=("value",)
    ))
    assert value == 42

    # Set attribute
    manager.access_object(instance, Operation(
        OperationType.SET_ATTRIBUTE,
        args=("value", 100)
    ))
    assert instance.value == 100

    # Call method
    result = manager.access_object(instance.method, Operation(
        OperationType.CALL,
        args=(5,)
    ))
    assert result == 10

    # Container operations
    item = manager.access_object(instance.items, Operation(
        OperationType.GET_ITEM,
        args=("a",)
    ))
    assert item == 1

    # Iteration
    iterator = manager.access_object(instance.items, Operation(
        OperationType.ITERATE
    ))
    assert set(iterator) == {"a", "b"}


def test_security_restrictions():
    security = OperationSecurity(
        allow_modification=False,
        allow_dynamic_access=False
    )
    manager = AccessManager(security)

    class TestClass:
        def __init__(self):
            self.value = 42

        def method(self):
            pass

    instance = TestClass()

    # Should fail: modification not allowed
    with pytest.raises(SecurityError):
        manager.access_object(instance, Operation(
            OperationType.SET_ATTRIBUTE,
            args=("value", 100)
        ))

    # Should fail: dynamic access not allowed
    with pytest.raises(SecurityError):
        manager.access_object(instance.method, Operation(
            OperationType.CALL
        ))
