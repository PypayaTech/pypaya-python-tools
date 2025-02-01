from typing import Any


class OperationError(Exception):
    """Base class for all operation-related errors."""
    def __init__(self, message: str, operation_type: str = None, details: dict = None):
        self.operation_type = operation_type
        self.details = details or {}
        super().__init__(message)


class SecurityError(OperationError):
    """Base class for security-related errors."""
    def __init__(self, message: str, restriction_type: str = None, **kwargs):
        super().__init__(
            message,
            operation_type="security",
            details={"restriction_type": restriction_type, **kwargs}
        )


class AccessSecurityError(SecurityError):
    """Raised when an operation violates security restrictions."""
    def __init__(self, message: str, access_type: str = None):
        super().__init__(message, restriction_type="access", access_type=access_type)


class ModificationSecurityError(SecurityError):
    """Raised when a modification operation is not allowed."""
    def __init__(self, message: str, modification_type: str = None):
        super().__init__(message, restriction_type="modification", modification_type=modification_type)


class ObjectAccessError(OperationError):
    """Base class for object access-related errors."""
    def __init__(self, message: str, attribute_name: str, **kwargs):
        super().__init__(
            message,
            operation_type="object_access",
            details={"attribute_name": attribute_name, **kwargs}
        )


class ObjectAttributeError(ObjectAccessError):
    """Raised when attribute access or modification fails."""
    pass


class CallError(OperationError):
    """Raised when calling an object fails."""
    def __init__(self, message: str, callable_name: str = None, args: tuple = None, kwargs: dict = None):
        super().__init__(
            message,
            operation_type="call",
            details={
                "callable_name": callable_name,
                "args": args,
                "kwargs": kwargs
            }
        )


class InstantiationError(OperationError):
    """Raised when class instantiation fails."""
    def __init__(self, message: str, class_name: str = None, args: tuple = None, kwargs: dict = None):
        super().__init__(
            message,
            operation_type="instantiation",
            details={
                "class_name": class_name,
                "args": args,
                "kwargs": kwargs
            }
        )


class ContainerError(OperationError):
    """Base class for container-related errors."""
    def __init__(self, message: str, container_type: str = None, key: Any = None, **kwargs):
        super().__init__(
            message,
            operation_type="container",
            details={"container_type": container_type, "key": key, **kwargs}
        )


class ItemAccessError(ContainerError):
    """Raised when accessing a container item fails."""
    pass


class ItemModificationError(ContainerError):
    """Raised when modifying a container item fails."""
    pass


class ItemDeletionError(ContainerError):
    """Raised when deleting a container item fails."""
    pass


class IterationError(OperationError):
    """Raised when iteration operations fail."""
    def __init__(self, message: str, iterable_type: str = None):
        super().__init__(
            message,
            operation_type="iteration",
            details={"iterable_type": iterable_type}
        )


class ValidationError(OperationError):
    """Raised when operation validation fails."""
    def __init__(self, message: str, validation_type: str = None, **kwargs):
        super().__init__(
            message,
            operation_type="validation",
            details={"validation_type": validation_type, **kwargs}
        )


class HandlerError(OperationError):
    """Raised when handler-related operations fail."""
    def __init__(self, message: str, handler_type: str = None):
        super().__init__(
            message,
            operation_type="handler",
            details={"handler_type": handler_type}
        )
