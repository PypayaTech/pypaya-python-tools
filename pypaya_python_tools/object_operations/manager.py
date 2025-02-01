from typing import Dict, Any, Optional
from pypaya_python_tools.object_operations.definitions import OperationType, Operation
from pypaya_python_tools.object_operations.exceptions import (
    OperationError,
    HandlerError
)
from pypaya_python_tools.object_operations.security import OperationSecurity
from pypaya_python_tools.object_operations.handlers.base import OperationHandler
from pypaya_python_tools.object_operations.handlers.attribute import AttributeHandler
from pypaya_python_tools.object_operations.handlers.call import CallHandler
from pypaya_python_tools.object_operations.handlers.direct import DirectHandler
from pypaya_python_tools.object_operations.handlers.instantiate import InstantiateHandler
from pypaya_python_tools.object_operations.handlers.container import ContainerHandler
from pypaya_python_tools.object_operations.handlers.iterator import IteratorHandler


class AccessManager:
    """Manages object access operations."""

    def __init__(self, security: Optional[OperationSecurity] = None):
        """Initialize manager with security settings and default handlers."""
        self.security = security or OperationSecurity()
        self.handlers: Dict[OperationType, OperationHandler] = {}

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register all default handlers."""
        self.register_handler(OperationType.INSTANTIATE, InstantiateHandler(self.security))
        self.register_handler(OperationType.CALL, CallHandler(self.security))
        self.register_handler(OperationType.GET_ATTRIBUTE, AttributeHandler(self.security))
        self.register_handler(OperationType.SET_ATTRIBUTE, AttributeHandler(self.security))
        self.register_handler(OperationType.DEL_ATTRIBUTE, AttributeHandler(self.security))
        self.register_handler(OperationType.DIRECT, DirectHandler(self.security))
        self.register_handler(OperationType.GET_ITEM, ContainerHandler(self.security))
        self.register_handler(OperationType.SET_ITEM, ContainerHandler(self.security))
        self.register_handler(OperationType.DEL_ITEM, ContainerHandler(self.security))
        self.register_handler(OperationType.ITERATE, IteratorHandler(self.security))

    def register_handler(
            self,
            operation_type: OperationType,
            handler: OperationHandler
    ) -> None:
        """Register a new operation handler.

        Args:
            operation_type: Type of operation to handle
            handler: Handler instance

        Raises:
            TypeError: If handler is invalid
        """
        if not isinstance(handler, OperationHandler):
            raise TypeError(f"Expected OperationHandler, got {type(handler)}")
        self.handlers[operation_type] = handler

    def access_object(self, obj: Any, operation: Operation) -> Any:
        """Access object according to operation specification.

        Args:
            obj: Object to operate on
            operation: Operation to perform

        Returns:
            Operation result value

        Raises:
            OperationError: If operation fails
            HandlerError: If no handler is found
        """
        handler = self.handlers.get(operation.type)
        if not handler:
            raise HandlerError(
                f"No handler for operation type: {operation.type}",
                handler_type=None
            )

        # Execute operation using handler's execute method
        result = handler.execute(obj, operation)
        return result.value

    def get_handler(
            self,
            operation_type: OperationType
    ) -> Optional[OperationHandler]:
        """Get handler for operation type."""
        return self.handlers.get(operation_type)

    def supports_operation(
            self,
            operation_type: OperationType
    ) -> bool:
        """Check if operation type is supported."""
        return operation_type in self.handlers
