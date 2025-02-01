import pytest
from pypaya_python_tools.object_operations.definitions import Operation, OperationType
from pypaya_python_tools.object_operations.handlers.call import CallHandler
from pypaya_python_tools.object_operations.security import OperationSecurity
from pypaya_python_tools.object_operations.exceptions import CallError, SecurityError


@pytest.fixture
def handler():
    return CallHandler(OperationSecurity(
        allow_dynamic_access=True
    ))


def test_can_handle(handler):
    def test_func():
        pass

    assert handler.can_handle(test_func, Operation(OperationType.CALL))
    assert handler.can_handle(lambda x: x, Operation(OperationType.CALL))
    assert not handler.can_handle("not_callable", Operation(OperationType.CALL))


def test_simple_call(handler):
    def test_func(x):
        return x * 2

    result = handler.handle(test_func, Operation(
        OperationType.CALL,
        args=(5,)
    ))
    assert result.success
    assert result.value == 10
    assert "callable" in result.metadata


def test_method_call(handler, test_object):
    result = handler.handle(test_object.method, Operation(
        OperationType.CALL,
        args=("test_arg",)
    ))
    assert result.success
    assert result.value == "method called with test_arg"
    assert result.metadata["is_method"]


def test_lambda_call(handler):
    func = lambda x, y: x + y
    result = handler.handle(func, Operation(
        OperationType.CALL,
        args=(2, 3)
    ))
    assert result.success
    assert result.value == 5


def test_call_with_kwargs(handler):
    def test_func(x, y=10):
        return x + y

    result = handler.handle(test_func, Operation(
        OperationType.CALL,
        args=(5,),
        kwargs={"y": 15}
    ))
    assert result.success
    assert result.value == 20


def test_invalid_arguments(handler):
    def test_func(x):
        return x

    with pytest.raises(CallError):
        handler.handle(test_func, Operation(
            OperationType.CALL,
            args=(1, 2, 3)  # Too many arguments
        ))


def test_call_security():
    secure_handler = CallHandler(OperationSecurity(
        allow_dynamic_access=False
    ))

    def test_func():
        pass

    with pytest.raises(SecurityError):
        secure_handler.handle(test_func, Operation(
            OperationType.CALL
        ))


def test_call_exception_handling(handler):
    def failing_func():
        raise ValueError("Test error")

    with pytest.raises(CallError) as exc_info:
        handler.handle(failing_func, Operation(
            OperationType.CALL
        ))
    assert "Test error" in str(exc_info.value)


def test_call_metadata(handler):
    def test_func(x, y):
        return x + y

    result = handler.handle(test_func, Operation(
        OperationType.CALL,
        args=(1, 2)
    ))

    assert result.metadata["callable"] == "test_func"
    assert "signature" in result.metadata
    assert result.metadata["is_function"]
    assert "module" in result.metadata
