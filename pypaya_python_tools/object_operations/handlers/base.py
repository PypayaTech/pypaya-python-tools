from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic, Optional, final
from pypaya_python_tools.object_operations.definitions import Operation, OperationResult, MetadataType
from pypaya_python_tools.object_operations.security import OperationSecurity
from pypaya_python_tools.object_operations.exceptions import (
    SecurityError, ValidationError, HandlerError, OperationError
)


T = TypeVar('T')  # Type of operation result
O = TypeVar('O')  # Type of object being operated on


class OperationHandler(Generic[T], ABC):
    """Base class for all operation handlers."""

    def __init__(self, security: OperationSecurity):
        self.security = security

    @abstractmethod
    def can_handle(self, obj: Any, op: Operation) -> bool:
        """Check if handler can handle this operation.

        Args:
            obj: Object to operate on
            op: Operation to perform

        Returns:
            bool: True if handler can handle this operation
        """
        pass

    @abstractmethod
    def handle(self, obj: O, op: Operation) -> OperationResult[T]:
        """Handle the operation.

        Args:
            obj: Object to operate on
            op: Operation to perform

        Returns:
            OperationResult containing the operation result

        Raises:
            OperationError: If operation fails
        """
        pass

    @final
    def execute(self, obj: O, op: Operation) -> OperationResult[T]:
        """Execute operation with validation and security checks.

        This method shouldn't be overridden - it provides the standard
        execution flow including validation and security checks.

        Args:
            obj: Object to operate on
            op: Operation to perform

        Returns:
            OperationResult containing the operation result

        Raises:
            ValidationError: If operation validation fails
            SecurityError: If security checks fail
            HandlerError: If handler execution fails
        """
        try:
            # Validate operation
            self._validate_operation(obj, op)

            # Check security
            self._check_security(obj, op)

            # Execute operation
            return self.handle(obj, op)

        except Exception as e:
            if isinstance(e, OperationError):
                raise
            raise HandlerError(
                str(e),
                handler_type=self.__class__.__name__
            ) from e

    def _validate_operation(self, obj: Any, op: Operation) -> None:
        """Validate operation before execution.

        Args:
            obj: Object to operate on
            op: Operation to perform

        Raises:
            ValidationError: If validation fails
        """
        if not self.can_handle(obj, op):
            raise ValidationError(
                f"Handler {self.__class__.__name__} cannot handle operation {op.type} "
                f"on object of type {type(obj).__name__}",
                validation_type="handler_compatibility"
            )

    def _check_security(self, obj: Any, op: Operation) -> None:
        """Perform security checks.

        Args:
            obj: Object to operate on
            op: Operation to perform

        Raises:
            SecurityError: If security checks fail
        """
        if not self.security.enabled:
            return

    def _create_result(
            self,
            success: bool,
            value: Optional[T] = None,
            error: Optional[Exception] = None,
            metadata: Optional[MetadataType] = None
    ) -> OperationResult[T]:
        """Create operation result with consistent structure.

        Args:
            success: Whether operation succeeded
            value: Operation result value
            error: Operation error if any
            metadata: Operation metadata

        Returns:
            OperationResult with provided data
        """
        return OperationResult(
            success=success,
            value=value,
            error=error,
            metadata=metadata or {}
        )
