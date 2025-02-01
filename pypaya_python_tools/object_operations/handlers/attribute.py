from typing import Any
from pypaya_python_tools.object_operations.definitions import (
    OperationType, Operation, OperationResult, MetadataType
)
from pypaya_python_tools.object_operations.exceptions import (
    ObjectAttributeError,
    ModificationSecurityError,
    SecurityError
)
from pypaya_python_tools.object_operations.handlers.base import OperationHandler


class AttributeHandler(OperationHandler[Any]):
    """Handles attribute operations (get/set/delete).

    Supports:
    - Getting attribute values
    - Setting attribute values
    - Deleting attributes
    - Property access
    """

    def can_handle(self, obj: Any, op: Operation) -> bool:
        """Check if operation is an attribute operation."""
        return op.type in (
            OperationType.GET_ATTRIBUTE,
            OperationType.SET_ATTRIBUTE,
            OperationType.DEL_ATTRIBUTE
        )

    def handle(self, obj: Any, op: Operation) -> OperationResult[Any]:
        """Handle attribute operations.

        Args:
            obj: Object to operate on
            op: Attribute operation to perform (GET_ATTRIBUTE, SET_ATTRIBUTE, or DEL_ATTRIBUTE)

        Returns:
            OperationResult containing:
            - For GET: attribute value
            - For SET: None
            - For DEL: None

        Raises:
            ObjectAttributeError: If attribute doesn't exist or operation fails
            ModificationSecurityError: If modification is not allowed
            SecurityError: If security restrictions prevent access

        Note:
            Temporarily stores the object being operated on for metadata creation.
            Any unexpected exceptions are wrapped in ObjectAttributeError.
        """
        self._current_obj = obj  # Store temporarily for metadata creation
        try:
            if op.type == OperationType.GET_ATTRIBUTE:
                return self._handle_get(obj, op)
            elif op.type == OperationType.SET_ATTRIBUTE:
                return self._handle_set(obj, op)
            else:  # DEL_ATTRIBUTE
                return self._handle_delete(obj, op)
        except Exception as e:
            if isinstance(e, (ObjectAttributeError, ModificationSecurityError, SecurityError)):
                raise
            raise ObjectAttributeError(
                f"Attribute operation failed: {str(e)}",
                attribute_name=op.args[0] if op.args else None
            )
        finally:
            self._current_obj = None  # Clean up

    def _handle_get(self, obj: Any, op: Operation) -> OperationResult[Any]:
        """Handle get attribute operation."""
        if not op.args:
            raise ObjectAttributeError(
                "Attribute name must be specified",
                attribute_name=None
            )

        attr_name = op.args[0]
        default = op.args[1] if len(op.args) > 1 else None

        # Validate attribute access
        self.security.validate_access(attr_name, is_method=False)

        # Handle attribute not found
        if not hasattr(obj, attr_name):
            if default is not None:
                return self._create_result(
                    success=True,
                    value=default,
                    metadata=self._create_attribute_metadata(attr_name, default)
                )
            raise ObjectAttributeError(
                f"Object has no attribute '{attr_name}'",
                attribute_name=attr_name
            )

        # Get attribute value
        value = getattr(obj, attr_name)
        return self._create_result(
            success=True,
            value=value,
            metadata=self._create_attribute_metadata(attr_name, value)
        )

    def _handle_set(self, obj: Any, op: Operation) -> OperationResult[None]:
        """Handle set attribute operation."""
        if len(op.args) < 2:
            raise ObjectAttributeError(
                "Attribute name and value must be specified",
                attribute_name=op.args[0] if op.args else None
            )

        if not self.security.allow_modification:
            raise ModificationSecurityError(
                "Attribute modification is not allowed",
                modification_type="set_attribute"
            )

        attr_name, value = op.args[:2]
        self.security.validate_access(attr_name, is_method=False)

        setattr(obj, attr_name, value)
        return self._create_result(
            success=True,
            metadata=self._create_attribute_metadata(attr_name, value, "set")
        )

    def _handle_delete(self, obj: Any, op: Operation) -> OperationResult[None]:
        """Handle delete attribute operation."""
        if not op.args:
            raise ObjectAttributeError(
                "Attribute name must be specified",
                attribute_name=None
            )

        if not self.security.allow_modification:
            raise ModificationSecurityError(
                "Attribute deletion is not allowed",
                modification_type="delete_attribute"
            )

        attr_name = op.args[0]
        self.security.validate_access(attr_name, is_method=False)

        if not hasattr(obj, attr_name):
            raise ObjectAttributeError(
                f"Cannot delete non-existent attribute '{attr_name}'",
                attribute_name=attr_name
            )

        delattr(obj, attr_name)
        return self._create_result(
            success=True,
            metadata=self._create_attribute_metadata(attr_name, None, "delete")
        )

    def _create_attribute_metadata(self, name: str, value: Any, operation: str = "get") -> MetadataType:
        return {
            "attribute": name,
            "type": type(value).__name__ if value is not None else None,
            "operation": operation,
            "has_property": isinstance(getattr(type(self._current_obj), name, None), property)
        }
