import logging
from typing import Any, Dict, List, Optional, Set, Type, Union, get_type_hints, Tuple
from pathlib import Path
import inspect
from dataclasses import is_dataclass
from enum import Enum

from pypaya_python_tools.importing import ImportManager
from pypaya_python_tools.importing.utils import import_object
from pypaya_python_tools.python_objects.base import PythonObject, ValidationError


class PythonClass(PythonObject[Type]):
    """Wrapper for Python classes."""

    def __init__(self, class_obj: Type) -> None:
        super().__init__(class_obj)

        # Analysis caches
        self._method_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._property_cache: Optional[Dict[str, Dict[str, Any]]] = None
        #self._class_vars_cache: Optional[Dict[str, Any]] = None
        #self._instance_vars_cache: Optional[Set[str]] = None

    def _validate_object(self, obj: Any) -> None:
        if not isinstance(obj, type):
            raise ValidationError(f"Expected class object, got {type(obj)}")

    # Properties
    @property
    def bases(self) -> Tuple[Type, ...]:
        """Get base classes."""
        return self._obj.__bases__

    @property
    def mro(self) -> Tuple[Type, ...]:
        """Get method resolution order."""
        return self._obj.__mro__

    @property
    def is_abstract(self) -> bool:
        return bool(getattr(self._obj, "__abstractmethods__", False))

    @property
    def is_dataclass(self) -> bool:
        return is_dataclass(self._obj)

    @property
    def is_enum(self) -> bool:
        return issubclass(self._obj, Enum)

    # Analysis methods
    def get_methods(self, include_private: bool = False) -> Dict[str, Function]:
        """Get all methods."""
        if self._method_cache is None:
            self._method_cache = {}
            for name, value in inspect.getmembers(self._obj, inspect.isfunction):
                if include_private or not name.startswith('_'):
                    self._method_cache[name] = Function(value)
        return self._method_cache.copy()

    def get_methodsOLD(self, include_private: bool = False) -> Dict[str, Dict[str, Any]]:
        """Get all methods."""
        if self._method_cache is None:
            self._method_cache = {}
            for name, value in inspect.getmembers(self.cls, predicate=inspect.isfunction):
                if include_private or not name.startswith('_'):
                    self._method_cache[name] = self._analyze_method(name, value)
        return self._method_cache.copy()

    def get_properties(self) -> Dict[str, Dict[str, Any]]:
        """Get all properties with access information."""
        if self._property_cache is None:
            self._property_cache = {}
            for name, value in inspect.getmembers(self._obj, lambda x: isinstance(x, property)):
                self._property_cache[name] = {
                    "has_getter": value.fget is not None,
                    "has_setter": value.fset is not None,
                    "has_deleter": value.fdel is not None,
                    "doc": value.__doc__
                }
        return self._property_cache.copy()

    def get_propertiesOLD(self) -> Dict[str, Dict[str, Any]]:
        """Get all properties with their details."""
        if self._property_cache is None:
            self._property_cache = {}
            for name, value in inspect.getmembers(self.cls, lambda x: isinstance(x, property)):
                self._property_cache[name] = {
                    "doc": value.__doc__,
                    "has_getter": value.fget is not None,
                    "has_setter": value.fset is not None,
                    "has_deleter": value.fdel is not None
                }
        return self._property_cache.copy()

    def get_attributes(self) -> Dict[str, Dict[str, Any]]:
        """Get class attributes and their types."""
        return {
            name: {
                "value": value,
                "type": type(value).__name__,
                "is_class_var": isinstance(value, ClassVar),
                "is_descriptor": hasattr(value, "__get__")
            }
            for name, value in vars(self._obj).items()
            if not (inspect.isfunction(value) or isinstance(value, (classmethod, staticmethod, property)))
        }

    # Creation methods
    @classmethod
    def from_module(cls, module_path: str, class_name: str) -> "PythonClass":
        """Create class from module import."""
        obj = import_object(module_path, class_name)
        if not isinstance(obj, type):
            raise ValidationError(f"{class_name} is not a class")
        return cls(obj)

    @classmethod
    def from_file(cls, file_path: Union[str, Path], class_name: str) -> "PythonClass":
        """Create class from file import."""
        obj = import_object(file_path, class_name)
        if not isinstance(obj, type):
            raise ValidationError(f"{class_name} is not a class")
        return cls(obj)

    # Instance creation
    def create_instance(self, *args: Any, **kwargs: Any) -> Any:
        """Create class instance with validation."""
        if self.is_abstract:
            raise ValidationError("Cannot instantiate abstract class")
        try:
            return self._obj(*args, **kwargs)
        except Exception as e:
            raise ValidationError(f"Instance creation failed: {str(e)}")

    # TODO add possibility of creating instance from config dict


    # Old methods, analyze if we need them or some interesting/useful patterns/code from them
    @property
    def cls(self) -> Type:
        """Get the wrapped class."""
        return self._obj

    def is_abstract(self) -> bool:
        """Check if the class is abstract."""
        # Direct ABC check
        if inspect.isabstract(self.cls):
            return True

        # Check for abstract methods/properties
        for name, value in inspect.getmembers(self.cls):
            if getattr(value, "__isabstractmethod__", False):
                return True

        return bool(getattr(self.cls, "__abstractmethods__", set()))

    def get_subclasses(self) -> Set[Type]:
        """Get all direct subclasses."""
        return set(self.cls.__subclasses__())

    def get_annotations(self) -> Dict[str, Any]:
        """Get type annotations for the class."""
        return getattr(self.cls, "__annotations__", {})

    def _analyze_method(self, name: str, method: Any) -> Dict[str, Any]:
        """Get detailed method information."""
        sig = inspect.signature(method)
        type_hints = get_type_hints(method, include_extras=True)

        return {
            "parameters": {
                name: {
                    "kind": param.kind.name,
                    "default": None if param.default is param.empty else param.default,
                    "annotation": str(type_hints.get(name, '')),
                    "has_default": param.default is not param.empty
                }
                for name, param in sig.parameters.items()
            },
            "return_type": str(type_hints.get("return", '')),
            "is_method": inspect.ismethod(method),
            "is_class_method": isinstance(method, classmethod),
            "is_static_method": isinstance(method, staticmethod),
            "is_property": isinstance(method, property),
            "has_varargs": any(p.kind == inspect.Parameter.VAR_POSITIONAL
                             for p in sig.parameters.values()),
            "has_varkw": any(p.kind == inspect.Parameter.VAR_KEYWORD
                            for p in sig.parameters.values()),
            "doc": method.__doc__
        }

    def get_class_variables(self) -> Dict[str, Any]:
        """Get all class-level variables."""
        if self._class_vars_cache is None:
            self._class_vars_cache = {
                name: value
                for name, value in vars(self.cls).items()
                if not (
                    inspect.isfunction(value) or
                    isinstance(value, (classmethod, staticmethod, property))
                )
            }
        return self._class_vars_cache.copy()

    def get_instance_variables(self) -> Set[str]:
        """Get names of instance variables."""
        if self._instance_vars_cache is None:
            self._instance_vars_cache = set()

            # Add __init__ parameters
            if hasattr(self.cls, "__init__"):
                init_sig = inspect.signature(self.cls.__init__)
                self._instance_vars_cache.update(
                    name for name in init_sig.parameters
                    if name != "self"
                )

            # Add annotated attributes
            self._instance_vars_cache.update(
                name for name in self.get_annotations()
                if not name.startswith('_')
            )

        return self._instance_vars_cache.copy()

    def instantiate(self, *args: Any, **kwargs: Any) -> Any:
        """
        Create an instance of the class.

        Args:
            *args: Positional arguments for constructor
            **kwargs: Keyword arguments for constructor

        Returns:
            Instance of the class

        Raises:
            ValidationError: If class is abstract
            TypeError: If arguments are invalid
        """
        if self.is_abstract():
            raise ValidationError("Cannot instantiate abstract class")

        try:
            return self.cls(*args, **kwargs)
        except Exception as e:
            raise TypeError(f"Failed to instantiate {self.name}: {str(e)}")

    @classmethod
    def from_path(cls, path: Union[str, Path], class_name: Optional[str] = None) -> "PythonClass":
        """
        Create class wrapper from module/file path.

        Args:
            path: Module or file path
            class_name: Optional class name if path is module

        Returns:
            PythonClass instance

        Raises:
            ValidationError: If class not found
            ImportError: If module cannot be imported
        """
        obj = import_object(path, class_name)
        if not isinstance(obj, type):
            raise ValidationError(f"Object '{class_name or path}' is not a class")
        return cls(obj)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PythonClass":
        """
        Create class from dictionary representation.

        Supports multiple creation methods:
        1. From module path: {"module_path": "package.module", "class_name": "MyClass"}
        2. From file path: {"file_path": "/path/to/file.py", "class_name": "MyClass"}

        Args:
            data: Dictionary containing creation information

        Returns:
            PythonClass instance

        Raises:
            ValidationError: If data is invalid or missing required fields
        """
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary")

        if "module_path" in data:
            return cls.from_path(data["module_path"], data.get("class_name"))
        elif "file_path" in data:
            return cls.from_path(Path(data["file_path"]), data.get("class_name"))
        else:
            raise ValidationError("Either module_path or file_path is required")


def create_instance(
        config: Union[Dict[str, Any], List[Dict[str, Any]]],
        base_path: Optional[str] = None,
        logger: Optional[logging.Logger] = None
) -> Any:
    """Create instance(s) from configuration.

    Args:
        config: Configuration dictionary or list of configurations.
            Must include one of:
            - 'module': str - module path (e.g., 'datetime')
            - 'file': str - file path
            May include:
            - 'class': str - class name (e.g., 'datetime')
            - 'args': list - positional arguments
            - 'kwargs': dict - keyword arguments
            - 'base_path': str - base path for imports
        base_path: Optional base path for imports
        logger: Optional logger instance

    Returns:
        Created object(s)
    """
    logger = logger or logging.getLogger(__name__)

    if isinstance(config, list):
        return [create_instance(item, base_path, logger) for item in config]

    if not isinstance(config, dict):
        return config

    # Validate inputs
    if "args" in config and not isinstance(config["args"], list):
        raise ValueError("'args' must be a list")
    if "kwargs" in config and not isinstance(config["kwargs"], dict):
        raise ValueError("'kwargs' must be a dictionary")
    if "class" in config and not isinstance(config["class"], str):
        raise ValueError("'class' must be a string")

    # Handle case where config is already an object
    if not any(key in config for key in ["module", "file", "class"]):
        return config

    try:
        # Extract configuration
        module_name = config.get("module")
        file_path = config.get("file")
        class_name = config.get("class")
        cfg_base_path = config.get("base_path", base_path)
        args = config.get("args", [])
        kwargs = config.get("kwargs", {})

        if not module_name and not file_path:
            raise ValueError("Must provide either 'module' or 'file'")

        # Import object
        if file_path:
            obj = ImportManager().import_from_file(path=file_path, name=class_name)
        else:
            obj = ImportManager().import_from_module(module=module_name, name=class_name)

        # Validate if class is abstract
        if inspect.isclass(obj) and inspect.isabstract(obj):
            raise ValueError(f"Cannot instantiate abstract class: {obj.__name__}")

        # Handle nested configurations
        args = [create_instance(arg, cfg_base_path, logger)
                if isinstance(arg, dict) else arg for arg in args]

        for key, value in list(kwargs.items()):
            if isinstance(value, dict):
                kwargs[key] = create_instance(value, cfg_base_path, logger)
            elif isinstance(value, list):
                kwargs[key] = [create_instance(item, cfg_base_path, logger)
                               if isinstance(item, dict) else item
                               for item in value]

        return obj(*args, **kwargs)

    except Exception as e:
        logger.error(f"Error creating instance: {str(e)}")
        raise




def main():
    # Example 1: Create a datetime object
    date_config = {
        "module": "datetime",
        "class": "datetime",
        "args": [2023, 6, 15],
        "kwargs": {"hour": 10, "minute": 30}
    }
    date_obj = create_instance(date_config)
    print("Example 1 - Datetime object:")
    print(f"Created date: {date_obj}")
    print(f"Type: {type(date_obj)}")
    print()

    # Example 2: Create a namedtuple
    namedtuple_config = {
        "module": "collections",
        "class": "namedtuple",
        "args": ["Person", "name age"],
    }
    Person = create_instance(namedtuple_config)
    john = Person("John", 30)
    print("Example 2 - Namedtuple:")
    print(f"Created namedtuple: {john}")
    print(f"Type: {type(john)}")
    print()

    # Example 3: Nested configuration
    nested_config = {
        "module": "collections",
        "class": "namedtuple",
        "args": ["Employee", "name position start_date"],
        "kwargs": {
            "defaults": [None, {
                "module": "datetime",
                "class": "date",
                "args": [2023, 6, 15]
            }]
        }
    }
    Employee = create_instance(nested_config)
    alice = Employee("Alice", "Developer")
    print("Example 3 - Nested configuration:")
    print(f"Created employee: {alice}")
    print(f"Type: {type(alice)}")
    print()

    # Example 4: Using package.subpackage.module (urllib.parse)
    urlparse_config = {
        "module": "urllib.parse",
        "class": "urlparse",
        "args": ["https://www.example.com/path?key=value"]
    }
    parsed_url = create_instance(urlparse_config)
    print("Example 4 - Using urllib.parse.urlparse:")
    print(f"Parsed URL: {parsed_url}")
    print(f"Scheme: {parsed_url.scheme}")
    print(f"Netloc: {parsed_url.netloc}")
    print(f"Path: {parsed_url.path}")
    print(f"Query: {parsed_url.query}")
    print(f"Type: {type(parsed_url)}")


if __name__ == "__main__":
    main()
