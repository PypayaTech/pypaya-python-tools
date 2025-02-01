import inspect
from typing import Any, Union, Callable
from pypaya_python_tools.object_operations.definitions import (
    OperationType, Operation, OperationResult, MetadataType
)
from pypaya_python_tools.object_operations.exceptions import (
    CallError, SecurityError
)
from pypaya_python_tools.object_operations.handlers.base import OperationHandler


class CallHandler(OperationHandler[Any]):
    """Handles callable object operations."""

    def can_handle(self, obj: Any, op: Operation) -> bool:
        return op.type == OperationType.CALL and callable(obj)

    def handle(self, obj: Union[Callable, Any], op: Operation) -> OperationResult[Any]:
        """Handle callable object invocation.

        Args:
            obj: Callable object to invoke
            op: Call operation specification

        Returns:
            OperationResult containing the call result

        Raises:
            CallError: If call fails
            SecurityError: If call is not allowed
        """
        try:
            if not self.security.allow_dynamic_access:
                raise SecurityError(
                    "Dynamic call operations are not allowed",
                    restriction_type="dynamic_call"
                )

            # Get function details
            func_name = self._get_callable_name(obj)
            sig = inspect.signature(obj)

            # Validate call
            self.security.validate_access(func_name, is_method=True)
            self._validate_call_args(obj, sig, op.args, op.kwargs)

            # Execute call
            result = obj(*op.args, **op.kwargs)

            return self._create_result(
                success=True,
                value=result,
                metadata=self._create_call_metadata(obj, sig, op, result)
            )

        except Exception as e:
            if isinstance(e, (CallError, SecurityError)):
                raise
            raise CallError(
                f"Call failed: {str(e)}",
                callable_name=self._get_callable_name(obj),
                args=op.args,
                kwargs=op.kwargs
            )

    def _get_callable_name(self, obj: Callable) -> str:
        """Get callable object's name."""
        return (
            obj.__name__ if hasattr(obj, "__name__")
            else obj.__class__.__name__
        )

    def _validate_call_args(
            self,
            obj: Callable,
            sig: inspect.Signature,
            args: tuple,
            kwargs: dict
    ) -> None:
        """Validate call arguments against signature."""
        try:
            sig.bind(*args, **kwargs)
        except TypeError as e:
            raise CallError(
                f"Invalid arguments for {self._get_callable_name(obj)}: {str(e)}",
                callable_name=self._get_callable_name(obj),
                args=args,
                kwargs=kwargs
            )

    def _create_call_metadata(
            self,
            obj: Callable,
            sig: inspect.Signature,
            op: Operation,
            result: Any
    ) -> MetadataType:
        """Create metadata for call operation."""
        return {
            "callable": self._get_callable_name(obj),
            "signature": str(sig),
            "args": repr(op.args),
            "kwargs": repr(op.kwargs),
            "result_type": type(result).__name__,
            "is_method": inspect.ismethod(obj),
            "is_function": inspect.isfunction(obj),
            "module": obj.__module__
        }
