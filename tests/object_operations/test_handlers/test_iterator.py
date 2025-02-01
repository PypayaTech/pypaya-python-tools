import pytest
from pypaya_python_tools.object_operations.definitions import Operation, OperationType
from pypaya_python_tools.object_operations.handlers.iterator import IteratorHandler
from pypaya_python_tools.object_operations.security import OperationSecurity
from pypaya_python_tools.object_operations.exceptions import IterationError


@pytest.fixture
def handler():
    return IteratorHandler(OperationSecurity())


def test_can_handle(handler):
    assert handler.can_handle([1, 2, 3], Operation(OperationType.ITERATE))
    assert handler.can_handle(range(5), Operation(OperationType.ITERATE))
    assert not handler.can_handle(42, Operation(OperationType.ITERATE))


def test_list_iteration(handler):
    test_list = [1, 2, 3]
    result = handler.handle(test_list, Operation(OperationType.ITERATE))
    assert result.success
    assert isinstance(result.value, type(iter([])))
    assert list(result.value) == test_list
    assert result.metadata["is_sequence"]
    assert result.metadata["has_length"]
    assert result.metadata["length"] == 3


def test_dict_iteration(handler):
    test_dict = {"a": 1, "b": 2}
    result = handler.handle(test_dict, Operation(OperationType.ITERATE))
    assert result.success
    assert list(result.value) == list(test_dict)
    assert result.metadata["is_mapping"]


def test_generator_iteration(handler):
    def gen():
        yield from range(3)

    result = handler.handle(gen(), Operation(OperationType.ITERATE))
    assert result.success
    assert list(result.value) == [0, 1, 2]
    assert result.metadata["is_generator"]
    assert not result.metadata["has_length"]


def test_set_iteration(handler):
    test_set = {1, 2, 3}
    result = handler.handle(test_set, Operation(OperationType.ITERATE))
    assert result.success
    assert set(result.value) == test_set


def test_custom_iterable(handler):
    class CustomIterable:
        def __iter__(self):
            return iter([1, 2, 3])

    obj = CustomIterable()
    result = handler.handle(obj, Operation(OperationType.ITERATE))
    assert result.success
    assert list(result.value) == [1, 2, 3]


def test_non_iterable(handler):
    with pytest.raises(IterationError):
        handler.handle(42, Operation(OperationType.ITERATE))


def test_failing_iterator(handler):
    class FailingIterable:
        def __iter__(self):
            raise ValueError("Iterator error")

    with pytest.raises(IterationError):
        handler.handle(FailingIterable(), Operation(OperationType.ITERATE))
