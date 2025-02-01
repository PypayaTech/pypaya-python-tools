from typing import Any
from pypaya_python_tools.object_operations.definitions import (
    OperationType, Operation, OperationResult, MetadataType
)
from pypaya_python_tools.object_operations.handlers.base import OperationHandler


class DirectHandler(OperationHandler[Any]):
    """Handles direct object access without modifications."""

    def can_handle(self, obj: Any, op: Operation) -> bool:
        return op.type == OperationType.DIRECT

    def handle(self, obj: Any, op: Operation) -> OperationResult[Any]:
        """Handle direct object access.

        Returns the object itself with metadata about its type and identity.
        """
        return self._create_result(
            success=True,
            value=obj,
            metadata=self._create_direct_metadata(obj)
        )

    def _create_direct_metadata(self, obj: Any) -> MetadataType:
        """Create metadata for direct object access."""
        return {
            "type": type(obj).__name__,
            "module": getattr(obj, "__module__", None),
            "id": id(obj),
            "qualname": getattr(type(obj), "__qualname__", None),
            "is_callable": callable(obj),
            "is_class": isinstance(obj, type),
            "is_module": hasattr(obj, "__file__")
        }
