import pytest
from pypaya_python_tools.object_operations.definitions import Operation, OperationType
from pypaya_python_tools.object_operations.handlers.direct import DirectHandler
from pypaya_python_tools.object_operations.security import OperationSecurity


@pytest.fixture
def handler():
    return DirectHandler(OperationSecurity())


def test_can_handle(handler):
    assert handler.can_handle(42, Operation(OperationType.DIRECT))
    assert handler.can_handle("string", Operation(OperationType.DIRECT))
    assert handler.can_handle(None, Operation(OperationType.DIRECT))


def test_direct_primitive(handler):
    result = handler.handle(42, Operation(OperationType.DIRECT))
    assert result.success
    assert result.value == 42
    assert result.metadata["type"] == "int"


def test_direct_string(handler):
    result = handler.handle("test", Operation(OperationType.DIRECT))
    assert result.success
    assert result.value == "test"
    assert result.metadata["type"] == "str"


def test_direct_object(handler, test_object):
    result = handler.handle(test_object, Operation(OperationType.DIRECT))
    assert result.success
    assert result.value == test_object
    assert result.metadata["type"] == "TestClass"
    assert result.metadata["is_class"] == False


def test_direct_class(handler):
    class TestClass:
        pass

    result = handler.handle(TestClass, Operation(OperationType.DIRECT))
    assert result.success
    assert result.metadata["is_class"] == True


def test_direct_metadata(handler):
    def test_func():
        pass

    result = handler.handle(test_func, Operation(OperationType.DIRECT))
    assert result.metadata["is_callable"]
    assert "module" in result.metadata
    assert "qualname" in result.metadata
