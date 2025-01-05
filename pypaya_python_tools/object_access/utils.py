from typing import Any, Optional, Dict, TypeVar, Type, Union, Callable, get_type_hints, List
from pathlib import Path
import logging
import inspect
from pypaya_python_tools.importing.definitions import ImportSource, SourceType
from pypaya_python_tools.importing.import_manager import ImportManager
from pypaya_python_tools.importing.utils import import_object
from pypaya_python_tools.object_access.definitions import AccessType, ObjectAccess
from pypaya_python_tools.object_access.access_manager import AccessManager


T = TypeVar('T')


# Basic object operations

def instantiate_class(cls: Type[T], *args, **kwargs) -> T:
    """Instantiate a class with given arguments."""
    access = ObjectAccess(
        type=AccessType.INSTANTIATE,
        args=args,
        kwargs=kwargs
    )
    return AccessManager().access_object(cls, access)


def call(obj: Any, *args, **kwargs) -> Any:
    """Call a callable object with arguments."""
    access = ObjectAccess(
        type=AccessType.CALL,
        args=args,
        kwargs=kwargs
    )
    return AccessManager().access_object(obj, access)


def get_attribute(obj: Any, name: str) -> Any:
    """Get object attribute by name."""
    access = ObjectAccess(
        type=AccessType.GET,
        args=(name,)
    )
    return AccessManager().access_object(obj, access)


def set_attribute(obj: Any, name: str, value: Any) -> None:
    """Set object attribute value."""
    access = ObjectAccess(
        type=AccessType.SET,
        args=(name, value)
    )
    return AccessManager().access_object(obj, access)


def configure_object(obj: Any, config: Dict[str, Any]) -> None:
    """Set multiple object attributes at once."""
    for key, value in config.items():
        set_attribute(obj, key, value)


# Combined import + access utilities

def import_and_instantiate(
        path: Union[str, Path],
        class_name: str,
        *args,
        **kwargs
) -> Any:
    """Import a class and create an instance."""
    cls = import_object(path, class_name)
    return instantiate_class(cls, *args, **kwargs)


def import_and_call(
        path: Union[str, Path],
        function_name: str,
        *args,
        **kwargs
) -> Any:
    """Import a function/callable and call it."""
    func = import_object(path, function_name)
    return call(func, *args, **kwargs)


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
            source = ImportSource(
                type=SourceType.FILE,
                location=file_path,
                name=class_name
            )
        else:
            source = ImportSource(
                type=SourceType.MODULE,
                location=module_name,
                name=class_name
            )

        obj = ImportManager().import_object(source)

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
