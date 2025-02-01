from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar
from pathlib import Path
import inspect


# Type for any Python object
T = TypeVar('T')


class ValidationError(Exception):
    """Raised when object validation fails."""
    pass


class PythonObject(Generic[T], ABC):
    """Base class for Python object wrappers."""

    def __init__(self, obj: T) -> None:
        self._validate_object(obj)
        self._obj = obj

    def _validate_object(self, obj: T) -> None:
        """Validate object before wrapping."""
        pass

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.qualname})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.qualname})"

    @property
    def obj(self) -> T:
        """Get wrapped object."""
        return self._obj

    @property
    def name(self) -> str:
        """Get object name."""
        return getattr(self._obj, "__name__", str(self._obj))

    @property
    def module(self) -> Optional[str]:
        """Get module name containing this object."""
        return getattr(self._obj, "__module__", None)

    @property
    def qualname(self) -> str:
        """Get qualified name of this object."""
        return getattr(self._obj, "__qualname__", self.name)

    @property
    def doc(self) -> Optional[str]:
        """Get object's docstring."""
        return getattr(self._obj, "__doc__", None)

    @property
    def file(self) -> Optional[Path]:
        """Get file containing this object's source."""
        try:
            return Path(inspect.getfile(self._obj))
        except (TypeError, ValueError):
            return None

    @property
    def source_location(self) -> Optional[Dict[str, Any]]:
        """Get source location information."""
        try:
            file = inspect.getfile(self._obj)
            lines, start_line = inspect.getsourcelines(self._obj)
            return {
                "file": file,
                "start_line": start_line,
                "end_line": start_line + len(lines) - 1
            }
        except (TypeError, OSError):
            return None

    def get_source(self) -> Optional[str]:
        """Get object's source code if available."""
        try:
            return inspect.getsource(self._obj)
        except (TypeError, OSError):
            return None

    def has_attribute(self, name: str) -> bool:
        """Check if object has an attribute."""
        return hasattr(self._obj, name)

    def get_attribute(self, name: str) -> Any:
        """Get object attribute by name."""
        if not hasattr(self._obj, name):
            raise AttributeError(f"Object has no attribute '{name}'")
        return getattr(self._obj, name)

    def set_attribute(self, name: str, value: Any) -> None:
        """Set object attribute value."""
        setattr(self._obj, name, value)

    @staticmethod
    def is_builtin(obj: Any) -> bool:
        """Check if object is built-in."""
        return obj.__module__ == "builtins"

    @staticmethod
    def get_definition_context(obj: Any) -> Dict[str, Any]:
        """Get context where object was defined."""
        return {
            "module": obj.__module__,
            "qualname": obj.__qualname__,
            "is_builtin": obj.__module__ == "builtins",
            "file": getattr(obj, "__file__", None)
        }

    @staticmethod
    def get_type_info(obj: Any) -> Dict[str, Any]:
        """Get detailed type information."""
        return {
            "type": type(obj).__name__,
            "mro": [cls.__name__ for cls in type(obj).__mro__],
            "is_class": isinstance(obj, type),
            "is_callable": callable(obj),
            "is_module": inspect.ismodule(obj),
            "is_function": inspect.isfunction(obj),
            "is_method": inspect.ismethod(obj)
        }
