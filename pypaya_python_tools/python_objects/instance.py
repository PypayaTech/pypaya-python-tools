from typing import Any, Dict, Type, Optional, Union, TypeVar, Generic, List
from pathlib import Path
import inspect
from dataclasses import is_dataclass

from pypaya_python_tools.importing import ImportManager
from pypaya_python_tools.importing.utils import import_object
from pypaya_python_tools.object_operations.definitions import OperationType, Operation
from pypaya_python_tools.object_operations.manager import AccessManager
from pypaya_python_tools.python_objects.base import PythonObject, ValidationError


T = TypeVar('T')


class Instance(PythonObject[T]):
    """Wrapper for Python object instances with creation and introspection capabilities."""

    def __init__(self, obj: T) -> None:
        super().__init__(obj)
        self._class_info = self._analyze_class()

    def _validate_object(self, obj: Any) -> None:
        """Ensure object is a class instance, not a class itself."""
        if isinstance(obj, type):
            raise ValidationError("Expected class instance, got class definition")

    def _analyze_class(self) -> Dict[str, Any]:
        """Analyze instance's class structure."""
        cls = type(self._obj)
        return {
            "name": cls.__name__,
            "module": cls.__module__,
            "is_dataclass": is_dataclass(cls),
            "is_builtin": self.is_builtin(cls),
            "has_slots": hasattr(cls, "__slots__"),
            "slots": getattr(cls, "__slots__", None),
            "is_hashable": hasattr(cls, "__hash__") and cls.__hash__ is not None
        }

    # Properties
    @property
    def class_type(self) -> Type[T]:
        """Get instance's class."""
        return type(self._obj)

    @property
    def is_dataclass_instance(self) -> bool:
        """Check if instance is a dataclass."""
        return self._class_info["is_dataclass"]

    @property
    def has_slots(self) -> bool:
        """Check if instance's class uses __slots__."""
        return self._class_info["has_slots"]

    # Instance analysis
    def get_instance_variables(self) -> Dict[str, Any]:
        """Get all instance variables and their values."""
        if self.has_slots:
            return {
                slot: getattr(self._obj, slot)
                for slot in self._class_info["slots"]
                if hasattr(self._obj, slot)
            }
        return {
            name: value
            for name, value in vars(self._obj).items()
            if not name.startswith('_')
        }

    def get_public_attributes(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all public attributes."""
        result = {}
        for name, value in inspect.getmembers(self._obj):
            if name.startswith('_'):
                continue

            result[name] = {
                "value": value,
                "type": type(value).__name__,
                "is_callable": callable(value),
                "is_property": isinstance(getattr(type(self._obj), name, None), property),
                "is_method": inspect.ismethod(value)
            }
        return result

    def get_state(self) -> Dict[str, Any]:
        """Get instance state (for pickling/serialization)."""
        if hasattr(self._obj, "__getstate__"):
            return self._obj.__getstate__()
        elif self.is_dataclass_instance:
            from dataclasses import asdict
            return asdict(self._obj)
        else:
            return self.get_instance_variables()

    # Creation methods
    @classmethod
    def from_class(
            cls,
            class_type: Type[T],
            *args: Any,
            **kwargs: Any
    ) -> "Instance[T]":
        """Create instance from class."""
        try:
            instance = class_type(*args, **kwargs)
            return cls(instance)
        except Exception as e:
            raise ValidationError(f"Failed to create instance: {str(e)}")

    @classmethod
    def from_import(
            cls,
            module_path: str,
            class_name: str,
            *args: Any,
            **kwargs: Any
    ) -> "Instance[T]":
        """Create instance by importing class and instantiating."""
        class_type = import_object(module_path, class_name)
        if not isinstance(class_type, type):
            raise ValidationError(f"{class_name} is not a class")
        return cls.from_class(class_type, *args, **kwargs)

    @classmethod
    def from_file(
            cls,
            file_path: Union[str, Path],
            class_name: str,
            *args: Any,
            **kwargs: Any
    ) -> "Instance[T]":
        """Create instance from class in file."""
        class_type = import_object(file_path, class_name)
        if not isinstance(class_type, type):
            raise ValidationError(f"{class_name} is not a class")
        return cls.from_class(class_type, *args, **kwargs)

    # Serialization support
    def to_config(self) -> Optional[Dict[str, Any]]:
        """Convert instance to configuration dictionary if possible."""
        if not self._class_info["is_builtin"]:
            return {
                "type": "class",
                "module": self._class_info["module"],
                "class": self._class_info["name"],
                "state": self.get_state()
            }
        return None

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "Instance":
        """Create instance from configuration dictionary."""
        if "type" not in config or config["type"] != "class":
            raise ValidationError("Invalid configuration format")

        if "module" not in config or "class" not in config:
            raise ValidationError("Configuration missing module or class name")

        instance = cls.from_import(config["module"], config["class"])

        if "state" in config and hasattr(instance.obj, "__setstate__"):
            instance.obj.__setstate__(config["state"])

        return instance

    # Operation support
    def __getattr__(self, name: str) -> Any:
        """Support attribute access on wrapped instance."""
        if name.startswith('_'):
            raise AttributeError(f"Access to private attribute '{name}' not allowed")

        access = Operation(
            type=OperationType.GET_ATTRIBUTE,
            args=(name,)
        )
        return AccessManager().access_object(self._obj, access)

    def __setattr__(self, name: str, value: Any) -> None:
        """Support attribute setting on wrapped instance."""
        if name.startswith('_'):
            # Allow setting private attributes on wrapper
            super().__setattr__(name, value)
            return

        access = Operation(
            type=OperationType.SET_ATTRIBUTE,
            args=(name, value)
        )
        AccessManager().access_object(self._obj, access)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Support calling instance if it's callable."""
        if not callable(self._obj):
            raise ValidationError("Instance is not callable")

        access = Operation(
            type=OperationType.CALL,
            args=args,
            kwargs=kwargs
        )
        return AccessManager().access_object(self._obj, access)





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
