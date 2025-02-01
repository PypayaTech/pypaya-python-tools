import pytest
from pypaya_python_tools.object_operations.definitions import (
    Operation, OperationResult, OperationType
)


def test_operation_creation():
    op = Operation(
        type=OperationType.GET_ATTRIBUTE,
        args=("test",),
        kwargs={"key": "value"}
    )
    assert op.type == OperationType.GET_ATTRIBUTE
    assert op.args == ("test",)
    assert op.kwargs == {"key": "value"}


def test_operation_immutable_args():
    op = Operation(
        type=OperationType.CALL,
        args=["test"],  # List instead of tuple
        kwargs={"key": "value"}
    )
    assert isinstance(op.args, tuple)
    assert op.args == ("test",)


def test_operation_result_success():
    result = OperationResult(success=True, value="test")
    assert result.success
    assert result.value == "test"
    assert result.error is None


def test_operation_result_failure():
    error = ValueError("test error")
    result = OperationResult(success=False, error=error)
    assert not result.success
    assert result.error == error
    assert result.value is None


def test_operation_result_invalid_state():
    with pytest.raises(ValueError):
        OperationResult(success=True, error=ValueError())

    with pytest.raises(ValueError):
        OperationResult(success=False)


def test_operation_metadata():
    op = Operation(
        type=OperationType.DIRECT,
        metadata={"test": "value"}
    )
    assert op.metadata == {"test": "value"}


def test_operation_result_metadata():
    result = OperationResult(
        success=True,
        value="test",
        metadata={"test": "value"}
    )
    assert result.metadata == {"test": "value"}
