from typing import Any
from pypaya_python_tools.object_operations.definitions import (
    OperationType, Operation, OperationResult, MetadataType
)
from pypaya_python_tools.object_operations.exceptions import (
    ItemAccessError, ItemModificationError, ItemDeletionError, SecurityError
)
from pypaya_python_tools.object_operations.handlers.base import OperationHandler


class ContainerHandler(OperationHandler[Any]):
    """Handles container operations (getitem, setitem, delitem)."""

    def can_handle(self, obj: Any, op: Operation) -> bool:
        return op.type in {
            OperationType.GET_ITEM,
            OperationType.SET_ITEM,
            OperationType.DEL_ITEM
        } and hasattr(obj, "__getitem__")

    def handle(self, obj: Any, op: Operation) -> OperationResult[Any]:
        """Handle container operations.

        Args:
            obj: Container object
            op: Container operation specification

        Returns:
            OperationResult containing:
            - For GET_ITEM: item value
            - For SET_ITEM: None
            - For DEL_ITEM: None

        Raises:
            ItemAccessError: If item access fails
            ItemModificationError: If item modification fails
            SecurityError: If operation is not allowed
        """
        try:
            if op.type == OperationType.GET_ITEM:
                return self._handle_get_item(obj, op)
            elif op.type == OperationType.SET_ITEM:
                return self._handle_set_item(obj, op)
            else:  # DEL_ITEM
                return self._handle_del_item(obj, op)

        except Exception as e:
            if isinstance(e, (ItemAccessError, ItemModificationError, SecurityError)):
                raise
            if op.type == OperationType.GET_ITEM:
                raise ItemAccessError(
                    f"Item access failed: {str(e)}",
                    container_type=type(obj).__name__,
                    key=op.args[0] if op.args else None
                )
            else:
                raise ItemModificationError(
                    f"Item modification failed: {str(e)}",
                    container_type=type(obj).__name__,
                    key=op.args[0] if op.args else None
                )

    def _handle_get_item(self, obj: Any, op: Operation) -> OperationResult[Any]:
        """Handle get item operation."""
        if not op.args:
            raise ItemAccessError(
                "Key must be specified",
                container_type=type(obj).__name__
            )

        key = op.args[0]
        value = obj[key]

        return self._create_result(
            success=True,
            value=value,
            metadata=self._create_item_metadata(obj, key, value, "get")
        )

    def _handle_set_item(self, obj: Any, op: Operation) -> OperationResult[None]:
        """Handle set item operation."""
        if len(op.args) < 2:
            raise ItemModificationError(
                "Key and value must be specified",
                container_type=type(obj).__name__
            )

        if not self.security.allow_modification:
            raise SecurityError(
                "Container modification is not allowed",
                restriction_type="container_modification"
            )

        key, value = op.args[:2]
        obj[key] = value

        return self._create_result(
            success=True,
            metadata=self._create_item_metadata(obj, key, value, "set")
        )

    def _handle_del_item(self, obj: Any, op: Operation) -> OperationResult[None]:
        """Handle delete item operation."""
        if not op.args:
            raise ItemDeletionError(
                "Key must be specified",
                container_type=type(obj).__name__
            )

        if not self.security.allow_modification:
            raise SecurityError(
                "Container modification is not allowed",
                restriction_type="container_modification"
            )

        key = op.args[0]
        try:
            del obj[key]
        except Exception as e:
            if isinstance(e, (ItemDeletionError, SecurityError)):  # Updated exception handling
                raise
            raise ItemDeletionError(
                f"Item deletion failed: {str(e)}",
                container_type=type(obj).__name__,
                key=key
            )

        return self._create_result(
            success=True,
            metadata=self._create_item_metadata(obj, key, None, "delete")
        )

    def _create_item_metadata(
            self,
            obj: Any,
            key: Any,
            value: Any,
            operation: str
    ) -> MetadataType:
        """Create metadata for container operations."""
        return {
            "container_type": type(obj).__name__,
            "key_type": type(key).__name__,
            "value_type": type(value).__name__ if value is not None else None,
            "operation": operation,
            "supports_sequence": isinstance(obj, (list, tuple)),
            "supports_mapping": isinstance(obj, dict)
        }
