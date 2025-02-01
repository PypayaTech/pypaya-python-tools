import inspect
from typing import Any, Type, TypeVar, cast
from pypaya_python_tools.object_operations.definitions import (
    OperationType, Operation, OperationResult, MetadataType
)
from pypaya_python_tools.object_operations.exceptions import (
    InstantiationError, SecurityError
)
from pypaya_python_tools.object_operations.handlers.base import OperationHandler

T = TypeVar('T')


class InstantiateHandler(OperationHandler[T]):
    """Handles class instantiation operations."""

    def can_handle(self, obj: Any, op: Operation) -> bool:
        return (op.type == OperationType.INSTANTIATE and
                isinstance(obj, type))

    def handle(self, obj: Type[T], op: Operation) -> OperationResult[T]:
        """Handle class instantiation.

        Args:
            obj: Class to instantiate
            op: Instantiation operation specification

        Returns:
            OperationResult containing the new instance

        Raises:
            InstantiationError: If instantiation fails
            SecurityError: If instantiation is not allowed
        """
        try:
            if not self.security.allow_dynamic_access:
                raise SecurityError(
                    "Dynamic instantiation is not allowed",
                    restriction_type="dynamic_instantiation"
                )

            cls = cast(Type[T], obj)

            # Validate class
            self._validate_class(cls)
            self.security.validate_access(cls.__name__, is_method=False)

            # Validate constructor args
            sig = inspect.signature(cls)
            self._validate_constructor_args(cls, sig, op.args, op.kwargs)

            # Create instance
            instance = cls(*op.args, **op.kwargs)

            return self._create_result(
                success=True,
                value=instance,
                metadata=self._create_instantiation_metadata(cls, sig, op)
            )

        except Exception as e:
            if isinstance(e, (InstantiationError, SecurityError)):
                raise
            raise InstantiationError(
                f"Instantiation failed: {str(e)}",
                class_name=obj.__name__,
                args=op.args,
                kwargs=op.kwargs
            )

    def _validate_class(self, cls: Type) -> None:
        """Validate that class can be instantiated."""
        if self._is_abstract(cls):
            raise InstantiationError(
                f"Cannot instantiate abstract class: {cls.__name__}",
                class_name=cls.__name__
            )

    def _is_abstract(self, cls: Type) -> bool:
        """Check if class is abstract."""
        # Check using inspect
        if inspect.isabstract(cls):
            return True

        # Check for abstractmethods
        for name, value in inspect.getmembers(cls):
            if getattr(value, "__isabstractmethod__", False):
                return True

        # Check __abstractmethods__ attribute
        abstract_methods = getattr(cls, "__abstractmethods__", set())
        return bool(abstract_methods)

    def _validate_constructor_args(
            self,
            cls: Type,
            sig: inspect.Signature,
            args: tuple,
            kwargs: dict
    ) -> None:
        """Validate constructor arguments."""
        try:
            sig.bind(*args, **kwargs)
        except TypeError as e:
            raise InstantiationError(
                f"Invalid arguments for {cls.__name__}: {str(e)}",
                class_name=cls.__name__,
                args=args,
                kwargs=kwargs
            )

    def _create_instantiation_metadata(
            self,
            cls: Type,
            sig: inspect.Signature,
            op: Operation
    ) -> MetadataType:
        """Create metadata for instantiation operation."""
        return {
            "class": cls.__name__,
            "module": cls.__module__,
            "signature": str(sig),
            "args": repr(op.args),
            "kwargs": repr(op.kwargs),
            "qualname": cls.__qualname__,
            "bases": tuple(base.__name__ for base in cls.__bases__),
            "is_dataclass": hasattr(cls, "__dataclass_fields__")
        }
