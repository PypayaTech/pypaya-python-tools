import inspect
from typing import Any, cast, Type
from pypaya_python_tools.importing.security import SecurityError
from pypaya_python_tools.object_access.definitions import AccessType, ObjectAccess
from pypaya_python_tools.object_access.exceptions import InstantiationError
from pypaya_python_tools.object_access.handlers.base import AccessHandler, AccessResult


class InstantiateHandler(AccessHandler):
    """Handles object instantiation."""

    def can_handle(self, obj: Any, access: ObjectAccess) -> bool:
        return (access.type == AccessType.INSTANTIATE and 
                isinstance(obj, type))

    def _is_abstract(self, cls: Type) -> bool:
        """
        Check if a class is abstract.

        A class is considered abstract if:
        1. It has abstractmethods (either through ABC or @abstractmethod)
        2. inspect.isabstract() returns True
        3. It has __abstractmethods__ attribute with non-empty set
        """
        # Check using inspect
        if inspect.isabstract(cls):
            return True

        # Check for abstractmethods
        for name, value in inspect.getmembers(cls):
            if getattr(value, '__isabstractmethod__', False):
                return True

        # Check __abstractmethods__ attribute
        abstract_methods = getattr(cls, '__abstractmethods__', set())
        if abstract_methods:
            return True

        return False

    def _validate_access(self, obj: Any, access: ObjectAccess) -> None:
        if not self.security.allow_dynamic_creation:
            raise SecurityError("Dynamic object creation is not allowed")

        if self._is_abstract(cast(Type, obj)):
            raise InstantiationError(f"Cannot instantiate abstract class: {obj.__name__}")

    def handle(self, obj: Any, access: ObjectAccess) -> AccessResult:
        self._validate_access(obj, access)

        try:
            instance = obj(*access.args, **access.kwargs)
            return AccessResult(
                instance,
                metadata={
                    "class": obj,
                    "args": access.args,
                    "kwargs": access.kwargs
                }
            )
        except Exception as e:
            raise InstantiationError(f"Failed to instantiate {obj.__name__}: {str(e)}")
