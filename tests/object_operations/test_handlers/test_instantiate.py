import pytest
from dataclasses import dataclass
from pypaya_python_tools.object_operations.definitions import Operation, OperationType
from pypaya_python_tools.object_operations.handlers.instantiate import InstantiateHandler
from pypaya_python_tools.object_operations.security import OperationSecurity
from pypaya_python_tools.object_operations.exceptions import InstantiationError, SecurityError


@pytest.fixture
def handler():
    return InstantiateHandler(OperationSecurity(
        allow_dynamic_access=True
    ))


def test_can_handle(handler):
    class TestClass:
        pass

    assert handler.can_handle(TestClass, Operation(OperationType.INSTANTIATE))
    assert not handler.can_handle(42, Operation(OperationType.INSTANTIATE))
    assert not handler.can_handle("string", Operation(OperationType.INSTANTIATE))


def test_simple_instantiation(handler):
    class TestClass:
        def __init__(self, value):
            self.value = value

    result = handler.handle(TestClass, Operation(
        OperationType.INSTANTIATE,
        args=(42,)
    ))
    assert result.success
    assert isinstance(result.value, TestClass)
    assert result.value.value == 42
    assert result.metadata["class"] == "TestClass"


def test_dataclass_instantiation(handler):
    @dataclass
    class TestDataClass:
        name: str
        value: int

    result = handler.handle(TestDataClass, Operation(
        OperationType.INSTANTIATE,
        args=("test", 42)
    ))
    assert result.success
    assert isinstance(result.value, TestDataClass)
    assert result.metadata["is_dataclass"]


def test_kwargs_instantiation(handler):
    class TestClass:
        def __init__(self, *, value):
            self.value = value

    result = handler.handle(TestClass, Operation(
        OperationType.INSTANTIATE,
        kwargs={"value": 42}
    ))
    assert result.success
    assert result.value.value == 42


def test_abstract_class(handler):
    from abc import ABC, abstractmethod

    class AbstractClass(ABC):
        @abstractmethod
        def method(self):
            pass

    with pytest.raises(InstantiationError):
        handler.handle(AbstractClass, Operation(OperationType.INSTANTIATE))


def test_invalid_arguments(handler):
    class TestClass:
        def __init__(self, value):
            self.value = value

    with pytest.raises(InstantiationError):
        handler.handle(TestClass, Operation(
            OperationType.INSTANTIATE,
            args=(1, 2, 3)  # Too many arguments
        ))


def test_security():
    class TestClass:
        pass

    secure_handler = InstantiateHandler(OperationSecurity(
        allow_dynamic_access=False
    ))

    with pytest.raises(SecurityError):
        secure_handler.handle(TestClass, Operation(
            OperationType.INSTANTIATE
        ))
