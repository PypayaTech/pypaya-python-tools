import inspect
from typing import Any, Callable
from pypaya_python_tools.object_access.definitions import AccessType, ObjectAccess
from pypaya_python_tools.object_access.exceptions import CallError
from pypaya_python_tools.object_access.exceptions import ObjectAccessSecurityError
from pypaya_python_tools.object_access.handlers.base import AccessHandler, AccessResult


class CallHandler(AccessHandler):
    """Handles callable objects."""

    def can_handle(self, obj: Any, access: ObjectAccess) -> bool:
        return (access.type == AccessType.CALL and
                callable(obj))

    def _validate_access(self, obj: Any, access: ObjectAccess) -> None:
        if not self.security.allow_dynamic_creation:
            raise ObjectAccessSecurityError("Dynamic execution is not allowed")

    def handle(self, obj: Any, access: ObjectAccess) -> AccessResult:
        self._validate_access(obj, access)

        try:
            # Get function signature for better error messages
            sig = inspect.signature(obj)
            try:
                # Validate arguments against signature
                sig.bind(*access.args, **access.kwargs)
            except TypeError as e:
                raise CallError(f"Invalid arguments for {obj.__name__}: {str(e)}")

            result = obj(*access.args, **access.kwargs)
            return AccessResult(
                result,
                metadata={
                    "callable": obj,
                    "args": access.args,
                    "kwargs": access.kwargs,
                    "signature": sig
                }
            )
        except Exception as e:
            if isinstance(e, CallError):
                raise
            raise CallError(f"Failed to call {getattr(obj, '__name__', str(obj))}: {str(e)}")
