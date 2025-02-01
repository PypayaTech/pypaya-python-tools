from typing import Any, Dict, Optional, get_type_hints, Union
from types import FunctionType
import inspect
from pathlib import Path
from pypaya_python_tools.importing.utils import import_object
from pypaya_python_tools.python_objects.base import PythonObject, ValidationError


class Function(PythonObject[FunctionType]):
    """Wrapper for Python functions, including regular functions and lambdas.

    Does not handle methods (instance, class, or static) - use Callable for those.
    Provides introspection, validation, and execution capabilities.
    """

    def __init__(self, obj: FunctionType) -> None:
        super().__init__(obj)
        self._signature: Optional[inspect.Signature] = None
        self._type_hints: Optional[Dict[str, Any]] = None

    def _validate_object(self, obj: Any) -> None:
        if not inspect.isfunction(obj):
            raise ValidationError(f"Expected function object, got {type(obj)}")

    # Core properties
    @property
    def signature(self) -> inspect.Signature:
        """Get function's signature."""
        if self._signature is None:
            self._signature = inspect.signature(self._obj)
        return self._signature

    @property
    def type_hints(self) -> Dict[str, Any]:
        """Get function's type hints."""
        if self._type_hints is None:
            try:
                self._type_hints = get_type_hints(self._obj)
            except Exception:
                self._type_hints = {}
        return self._type_hints.copy()

    @property
    def is_generator(self) -> bool:
        """Check if function is a generator function."""
        return inspect.isgeneratorfunction(self._obj)

    @property
    def is_coroutine(self) -> bool:
        """Check if function is a coroutine function."""
        return inspect.iscoroutinefunction(self._obj)

    @property
    def is_async_generator(self) -> bool:
        """Check if function is an async generator function."""
        return inspect.isasyncgenfunction(self._obj)

    @property
    def is_lambda(self) -> bool:
        """Check if function is a lambda function."""
        return self._obj.__name__ == "<lambda>"

    @property
    def can_serialize(self) -> bool:
        """Check if function can be serialized to config."""
        if self.is_lambda:
            return False
        return (hasattr(self._obj, "__module__") and
                hasattr(self._obj, "__qualname__"))

    # Creation methods
    @classmethod
    def from_module(cls, module_path: str, function_name: str) -> "Function":
        """Create function from module import."""
        obj = import_object(module_path, function_name)
        if not inspect.isfunction(obj):
            raise ValidationError(f"{function_name} is not a function")
        return cls(obj)

    @classmethod
    def from_file(cls, file_path: Union[str, Path], function_name: str) -> "Function":
        """Create function from file import."""
        obj = import_object(file_path, function_name)
        if not inspect.isfunction(obj):
            raise ValidationError(f"{function_name} is not a function")
        return cls(obj)

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "Function":
        """Create function from configuration dictionary.

        Config format:
        {
            "type": "module"|"file",
            "location": str,  # module path or file path
            "name": str      # function name
        }
        """
        if "type" not in config or "location" not in config or "name" not in config:
            raise ValidationError("Config must specify type, location, and name")

        if config["type"] == "module":
            return cls.from_module(config["location"], config["name"])
        elif config["type"] == "file":
            return cls.from_file(config["location"], config["name"])
        else:
            raise ValidationError(f"Unknown import type: {config['type']}")

    def to_config(self) -> Optional[Dict[str, Any]]:
        """Convert function to configuration dictionary."""
        if not self.can_serialize:
            return None

        return {
            "type": "module",
            "location": self._obj.__module__,
            "name": self._obj.__qualname__
        }

    # Validation methods
    def validate_call(self, *args: Any, **kwargs: Any) -> bool:
        """Validate arguments without executing."""
        try:
            self.signature.bind(*args, **kwargs)
            return True
        except TypeError:
            return False

    def bind_arguments(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Bind arguments to parameter names."""
        bound = self.signature.bind(*args, **kwargs)
        bound.apply_defaults()
        return bound.arguments

    # Execution
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute function with argument validation."""
        if not self.validate_call(*args, **kwargs):
            raise ValidationError("Invalid arguments")
        return self._obj(*args, **kwargs)
