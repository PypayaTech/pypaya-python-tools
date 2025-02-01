import pytest
from pypaya_python_tools.object_operations.definitions import Operation, OperationType
from pypaya_python_tools.object_operations.handlers.attribute import AttributeHandler
from pypaya_python_tools.object_operations.security import OperationSecurity
from pypaya_python_tools.object_operations.exceptions import ObjectAttributeError, ModificationSecurityError, \
    SecurityError


@pytest.fixture
def handler():
    return AttributeHandler(OperationSecurity(
        allow_private_access=True,
        allow_protected_access=True,
        allow_modification=True
    ))


def test_can_handle(handler, test_object):
    assert handler.can_handle(test_object, Operation(OperationType.GET_ATTRIBUTE))
    assert handler.can_handle(test_object, Operation(OperationType.SET_ATTRIBUTE))
    assert handler.can_handle(test_object, Operation(OperationType.DEL_ATTRIBUTE))
    assert not handler.can_handle(test_object, Operation(OperationType.CALL))


def test_get_attribute(handler, test_object):
    # Public attribute
    result = handler.handle(test_object, Operation(
        OperationType.GET_ATTRIBUTE,
        args=("public",)
    ))
    assert result.success
    assert result.value == "public"
    assert "attribute" in result.metadata

    # Protected attribute
    result = handler.handle(test_object, Operation(
        OperationType.GET_ATTRIBUTE,
        args=("_protected",)
    ))
    assert result.success
    assert result.value == "protected"

    # Property
    result = handler.handle(test_object, Operation(
        OperationType.GET_ATTRIBUTE,
        args=("prop",)
    ))
    assert result.success
    assert result.value == "property value"
    assert result.metadata["has_property"]


def test_get_attribute_with_default(handler, test_object):
    result = handler.handle(test_object, Operation(
        OperationType.GET_ATTRIBUTE,
        args=("nonexistent", "default")
    ))
    assert result.success
    assert result.value == "default"


def test_get_nonexistent_attribute(handler, test_object):
    with pytest.raises(ObjectAttributeError):
        handler.handle(test_object, Operation(
            OperationType.GET_ATTRIBUTE,
            args=("nonexistent",)
        ))


def test_set_attribute(handler, test_object):
    result = handler.handle(test_object, Operation(
        OperationType.SET_ATTRIBUTE,
        args=("public", "new_value")
    ))
    assert result.success
    assert test_object.public == "new_value"
    assert result.metadata["operation"] == "set"


def test_set_attribute_without_modification_permission(test_object):
    restricted_handler = AttributeHandler(OperationSecurity(allow_modification=False))
    with pytest.raises(ModificationSecurityError):
        restricted_handler.handle(test_object, Operation(
            OperationType.SET_ATTRIBUTE,
            args=("public", "new_value")
        ))


def test_delete_attribute(handler, test_object):
    # Add a new attribute to delete
    test_object.temp = "temporary"
    result = handler.handle(test_object, Operation(
        OperationType.DEL_ATTRIBUTE,
        args=("temp",)
    ))
    assert result.success
    assert not hasattr(test_object, "temp")
    assert result.metadata["operation"] == "delete"


def test_delete_nonexistent_attribute(handler, test_object):
    with pytest.raises(ObjectAttributeError):
        handler.handle(test_object, Operation(
            OperationType.DEL_ATTRIBUTE,
            args=("nonexistent",)
        ))


def test_attribute_security(test_object):
    secure_handler = AttributeHandler(OperationSecurity(
        allow_private_access=False,
        allow_protected_access=False
    ))

    # Protected attribute
    with pytest.raises(SecurityError):
        secure_handler.handle(test_object, Operation(
            OperationType.GET_ATTRIBUTE,
            args=("_protected",)
        ))

    # Private attribute
    with pytest.raises(SecurityError):
        secure_handler.handle(test_object, Operation(
            OperationType.GET_ATTRIBUTE,
            args=("__private",)
        ))
