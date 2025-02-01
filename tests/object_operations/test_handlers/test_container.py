import pytest
from pypaya_python_tools.object_operations.definitions import Operation, OperationType
from pypaya_python_tools.object_operations.handlers.container import ContainerHandler
from pypaya_python_tools.object_operations.security import OperationSecurity
from pypaya_python_tools.object_operations.exceptions import (
    ItemAccessError, ItemModificationError, SecurityError
)


@pytest.fixture
def handler():
    return ContainerHandler(OperationSecurity(
        allow_modification=True,
        allow_container_modification=True
    ))


def test_can_handle(handler, test_dict, test_list):
    assert handler.can_handle(test_dict, Operation(OperationType.GET_ITEM))
    assert handler.can_handle(test_list, Operation(OperationType.SET_ITEM))
    assert handler.can_handle(test_dict, Operation(OperationType.DEL_ITEM))
    assert not handler.can_handle(42, Operation(OperationType.GET_ITEM))


def test_get_item_dict(handler, test_dict):
    result = handler.handle(test_dict, Operation(
        OperationType.GET_ITEM,
        args=("a",)
    ))
    assert result.success
    assert result.value == 1
    assert result.metadata["container_type"] == "dict"
    assert result.metadata["key_type"] == "str"


def test_get_item_list(handler, test_list):
    result = handler.handle(test_list, Operation(
        OperationType.GET_ITEM,
        args=(0,)
    ))
    assert result.success
    assert result.value == 1
    assert result.metadata["container_type"] == "list"
    assert result.metadata["supports_sequence"]


def test_set_item_dict(handler, test_dict):
    result = handler.handle(test_dict, Operation(
        OperationType.SET_ITEM,
        args=("a", 100)
    ))
    assert result.success
    assert test_dict["a"] == 100
    assert result.metadata["operation"] == "set"


def test_set_item_list(handler, test_list):
    result = handler.handle(test_list, Operation(
        OperationType.SET_ITEM,
        args=(0, 100)
    ))
    assert result.success
    assert test_list[0] == 100


def test_del_item_dict(handler, test_dict):
    result = handler.handle(test_dict, Operation(
        OperationType.DEL_ITEM,
        args=("a",)
    ))
    assert result.success
    assert "a" not in test_dict
    assert result.metadata["operation"] == "delete"


def test_del_item_list(handler, test_list):
    original_length = len(test_list)
    result = handler.handle(test_list, Operation(
        OperationType.DEL_ITEM,
        args=(0,)
    ))
    assert result.success
    assert len(test_list) == original_length - 1


def test_invalid_key(handler, test_dict):
    with pytest.raises(ItemAccessError):
        handler.handle(test_dict, Operation(
            OperationType.GET_ITEM,
            args=("nonexistent",)
        ))


def test_modification_security(test_dict):
    secure_handler = ContainerHandler(OperationSecurity(
        allow_modification=False
    ))

    with pytest.raises(SecurityError):
        secure_handler.handle(test_dict, Operation(
            OperationType.SET_ITEM,
            args=("a", 100)
        ))


def test_custom_container(handler, container_object):
    result = handler.handle(container_object, Operation(
        OperationType.GET_ITEM,
        args=("a",)
    ))
    assert result.success
    assert result.value == 1
