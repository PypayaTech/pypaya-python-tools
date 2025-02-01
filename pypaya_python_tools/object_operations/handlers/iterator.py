from typing import Any, Iterator
from pypaya_python_tools.object_operations.definitions import (
    OperationType, Operation, OperationResult, MetadataType
)
from pypaya_python_tools.object_operations.exceptions import IterationError
from pypaya_python_tools.object_operations.handlers.base import OperationHandler


class IteratorHandler(OperationHandler[Iterator]):
    """Handles iteration operations."""

    def can_handle(self, obj: Any, op: Operation) -> bool:
        return (op.type == OperationType.ITERATE and
                hasattr(obj, "__iter__"))

    def handle(self, obj: Any, op: Operation) -> OperationResult[Iterator]:
        """Handle iteration operation.

        Args:
            obj: Iterable object
            op: Iteration operation specification

        Returns:
            OperationResult containing the iterator

        Raises:
            IterationError: If iteration fails
        """
        try:
            iterator = iter(obj)
            return self._create_result(
                success=True,
                value=iterator,
                metadata=self._create_iterator_metadata(obj)
            )
        except Exception as e:
            if isinstance(e, IterationError):
                raise
            raise IterationError(
                f"Iteration failed: {str(e)}",
                iterable_type=type(obj).__name__
            )

    def _create_iterator_metadata(self, obj: Any) -> MetadataType:
        """Create metadata for iteration operation."""
        return {
            "iterable_type": type(obj).__name__,
            "is_generator": hasattr(obj, "__next__"),
            "is_sequence": isinstance(obj, (list, tuple)),
            "is_mapping": isinstance(obj, dict),
            "has_length": hasattr(obj, "__len__"),
            "length": len(obj) if hasattr(obj, "__len__") else None
        }
