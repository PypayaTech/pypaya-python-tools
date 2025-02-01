from enum import Enum, auto
from typing import Any, Dict, Optional, Type, Callable as CallableType, Union
import inspect
from pathlib import Path
from functools import partial
from pypaya_python_tools.importing.utils import import_object
from pypaya_python_tools.python_objects.base import PythonObject, ValidationError


class CallableKind(Enum):
    """Fundamental structural types of callables."""
    FUNCTION = auto()         # Regular function
    LAMBDA = auto()           # Lambda function
    METHOD = auto()           # Instance method
    CLASS_METHOD = auto()     # Class method
    STATIC_METHOD = auto()    # Static method
    PROPERTY = auto()         # Property
    BUILTIN_FUNCTION = auto() # Built-in function
    BUILTIN_METHOD = auto()   # Built-in method
    PARTIAL = auto()          # Partial function
    CALLABLE_CLASS = auto()   # Class with __call__

    @classmethod
    def from_object(cls, obj: Any) -> "CallableKind":
        """Determine callable's structural type."""
        if isinstance(obj, (staticmethod, classmethod, property)):
            obj = obj.__get__(None, type)

        if isinstance(obj, property):
            return cls.PROPERTY
        elif isinstance(obj, partial):
            return cls.PARTIAL
        elif isinstance(obj, type) and hasattr(obj, "__call__"):
            return cls.CALLABLE_CLASS
        elif isinstance(obj, (staticmethod, classmethod)):
            return cls.CLASS_METHOD if isinstance(obj, classmethod) else cls.STATIC_METHOD
        elif inspect.ismethod(obj):
            return cls.METHOD
        elif inspect.isfunction(obj):
            return cls.LAMBDA if obj.__name__ == "<lambda>" else cls.FUNCTION
        elif inspect.isbuiltin(obj):
            return cls.BUILTIN_METHOD if inspect.ismethod(obj) else cls.BUILTIN_FUNCTION
        else:
            return cls.CALLABLE_CLASS if hasattr(obj, "__call__") else cls.FUNCTION


class Callable(PythonObject[CallableType]):
    """Universal wrapper for callable objects.

    Handles all types of callable objects:
    - Functions (regular and lambda)
    - Methods (instance, class, and static)
    - Properties
    - Built-in functions and methods
    - Partial functions
    - Classes with __call__
    """

    def __init__(self, obj: Any) -> None:
        super().__init__(obj)
        self._kind = CallableKind.from_object(obj)
        self._signature: Optional[inspect.Signature] = None
        self._owner: Optional[Type] = self._get_owner()
        self._instance: Optional[Any] = self._get_instance()

    def _validate_object(self, obj: Any) -> None:
        if not callable(obj):
            raise ValidationError(f"Object {obj} is not callable")

    def _get_owner(self) -> Optional[Type]:
        """Get owner class for methods."""
        if inspect.ismethod(self._obj):
            return self._obj.__self__.__class__
        elif hasattr(self._obj, "__qualname__"):
            parts = self._obj.__qualname__.split('.')
            if len(parts) > 1:
                try:
                    return getattr(self._obj, "__objclass__", None)
                except Exception:
                    return None
        return None

    def _get_instance(self) -> Optional[Any]:
        """Get instance for bound methods."""
        return getattr(self._obj, "__self__", None) if inspect.ismethod(self._obj) else None

    # Core properties
    @property
    def kind(self) -> CallableKind:
        """Get the kind of callable."""
        return self._kind

    @property
    def signature(self) -> inspect.Signature:
        """Get callable's signature."""
        if self._signature is None:
            self._signature = inspect.signature(self._obj)
        return self._signature

    @property
    def owner(self) -> Optional[Type]:
        """Get owner class for methods."""
        return self._owner

    @property
    def instance(self) -> Optional[Any]:
        """Get instance for bound methods."""
        return self._instance

    @property
    def can_serialize(self) -> bool:
        """Check if callable can be serialized to config."""
        if self.kind in {CallableKind.LAMBDA, CallableKind.PARTIAL}:
            return False
        return (hasattr(self._obj, "__module__") and
                hasattr(self._obj, "__qualname__"))

    # Creation methods
    @classmethod
    def from_module(cls, module_path: str, callable_name: str) -> "Callable":
        """Create callable from module import."""
        obj = import_object(module_path, callable_name)
        if not callable(obj):
            raise ValidationError(f"{callable_name} is not callable")
        return cls(obj)

    @classmethod
    def from_file(cls, file_path: Union[str, Path], callable_name: str) -> "Callable":
        """Create callable from file import."""
        obj = import_object(file_path, callable_name)
        if not callable(obj):
            raise ValidationError(f"{callable_name} is not callable")
        return cls(obj)

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "Callable":
        """Create callable from configuration dictionary."""
        if "type" not in config or "location" not in config or "name" not in config:
            raise ValidationError("Config must specify type, location, and name")

        if config["type"] == "module":
            return cls.from_module(config["location"], config["name"])
        elif config["type"] == "file":
            return cls.from_file(config["location"], config["name"])
        # TODO What if we want to create callable by creating instance of class based on dict?
        # Maybe Instance class with its creation method could be used?
        # It is important scenario

        # elif config["type"] == "class":
        #     from pypaya_python_tools.python_objects.klass import PythonClass
        #     instance_config = {
        #         "args": config.get("args", []),
        #         "kwargs": config.get("kwargs", {})
        #     }
        #     if "." in config["location"] or "/" not in config["location"]:
        #         instance_config["module"] = config["location"]
        #     else:
        #         instance_config["file"] = config["location"]
        #     instance_config["class"] = config["name"]
        #     return cls(PythonClass.create_instance_from_config(instance_config))
        # elif config["type"] == "partial":
        #     base_func = import_object(
        #         config["func"]["location"],
        #         config["func"]["name"]
        #     )
        #     return cls(partial(
        #         base_func,
        #         *config.get("args", []),
        #         **config.get("kwargs", {})
        #     ))
        else:
            raise ValidationError(f"Unknown import type: {config['type']}")

    def to_config(self) -> Optional[Dict[str, Any]]:
        """Convert callable to configuration dictionary."""
        if not self.can_serialize:
            return None

        return {
            "type": "module",
            "location": self._obj.__module__,
            "name": self._obj.__qualname__
        }

    # Validation and execution
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

    # def is_compatible_with(self, other: "Callable") -> bool:
    #     """Check if callable signatures are compatible."""
    #     return self.signature.parameters == other.signature.parameters

    # Manipulation methods
    def create_partial(self, *args: Any, **kwargs: Any) -> "Callable":
        """Create new Callable with partial application."""
        return Callable(partial(self._obj, *args, **kwargs))

    # def bind_instance(self, instance: Any) -> "Callable": # TODO What this does?
    #     """Bind this callable to an instance."""
    #     if self._kind not in (CallableKind.METHOD, CallableKind.CLASS_METHOD):
    #         raise ValidationError(
    #             f"Cannot bind {self._kind.name} to instance"
    #         )
    #
    #     try:
    #         bound = self._obj.__get__(instance, type(instance))
    #         return Callable(bound)
    #     except AttributeError as e:
    #         raise ValidationError(f"Failed to bind: {str(e)}")

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute callable with argument validation."""
        if not self.validate_call(*args, **kwargs):
            raise ValidationError("Invalid arguments")
        return self._obj(*args, **kwargs)
