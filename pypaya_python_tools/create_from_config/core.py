import functools
from typing import Any, Union, Optional, List, Dict, TypeVar, Type, Callable
import inspect
from pypaya_python_tools.create_from_config.exceptions import (
    ConfigError,
    ValidationError,
    ImportConfigError,
    InstantiationError,
    CallableCreationError
)
from pypaya_python_tools.importing import import_object, ImportSecurity


T = TypeVar('T')


def create_instance(
    config: Union[Dict[str, Any], List[Dict[str, Any]]],
    expected_type: Type[T] = None,
    security: Optional[ImportSecurity] = None
) -> Any:
    """
    Create class instance(s) from configuration.

    Args:
        config: Configuration dictionary or list of configurations.
            Must include one of:
            - 'module': str - module path (e.g., 'datetime')
            - 'file': str - file path
            Must include:
            - 'class': str - class name
            May include:
            - 'args': list - positional arguments
            - 'kwargs': dict - keyword arguments
        expected_type: Optional type to validate against
        security: Optional import security settings. By default:
            - File imports are allowed
            - All other security settings at their defaults

    Returns:
        Created instance(s)

    Raises:
        ConfigError: If configuration is invalid
        InstantiationError: If instance creation fails
        ValidationError: If type validation fails
    """
    # Set default security settings
    if security is None:
        security = ImportSecurity(allow_file_imports=True)

    # Handle list of configurations
    if isinstance(config, list):
        return [create_instance(item, expected_type, security) for item in config]

    # Handle direct values
    if not isinstance(config, dict):
        return config

    try:
        # Validate config
        if not isinstance(config.get("args", []), (list, tuple)):
            raise ValidationError("'args' must be a list or tuple")
        if not isinstance(config.get("kwargs", {}), dict):
            raise ValidationError("'kwargs' must be a dictionary")
        if "class" not in config:
            raise ValidationError("Configuration must include 'class'")
        if not isinstance(config["class"], str):
            raise ValidationError("'class' must be a string")
        if "module" not in config and "file" not in config:
            raise ValidationError("Must provide either 'module' or 'file'")

        # Import class
        if "file" in config:
            cls = import_object(config["file"], config["class"], security=security)
        else:
            cls = import_object(f"{config['module']}.{config['class']}", security=security)

        # Validate it's a class
        if not isinstance(cls, type):
            raise InstantiationError(f"'{config['class']}' is not a class")

        # Check if abstract
        if inspect.isabstract(cls):
            raise InstantiationError(f"Cannot instantiate abstract class: {cls.__name__}")

        # Process arguments
        args = config.get("args", [])
        kwargs = config.get("kwargs", {})

        # Handle nested configurations
        args = [
            create_instance(arg, None, security) if isinstance(arg, dict) else arg
            for arg in args
        ]
        kwargs = {
            key: create_instance(value, None, security) if isinstance(value, dict) else value
            for key, value in kwargs.items()
        }

        # Create instance
        instance = cls(*args, **kwargs)

        # Validate type if needed
        if expected_type and not isinstance(instance, expected_type):
            raise ValidationError(
                f"Created instance is of type {type(instance)}, expected {expected_type}"
            )

        return instance

    except (ConfigError, ValidationError):
        raise
    except Exception as e:
        raise InstantiationError(f"Failed to create instance: {str(e)}") from e


def create_callable(config: Dict[str, Any]) -> Callable:
    """
    Create callable from configuration.

    Supports three main cases:
    1. Direct callable import (function, built-in, etc.)
    2. Instance method (including classes with __call__)
    3. Partial function

    Args:
        config: Configuration dictionary with either:
            - module/name for direct callable
            - class config + optional method name
            - partial configuration

    Returns:
        Callable object

    Raises:
        ConfigError: If configuration is invalid
        CallableCreationError: If callable creation fails
    """
    try:
        if "partial" in config:
            # Handle partial case
            partial_config = config["partial"]
            func = create_callable(partial_config["function"])
            args = partial_config.get("args", [])
            kwargs = partial_config.get("kwargs", {})

            # Handle nested configurations in args/kwargs
            args = [
                create_instance(arg) if isinstance(arg, dict) else arg
                for arg in args
            ]
            kwargs = {
                key: create_instance(value) if isinstance(value, dict) else value
                for key, value in kwargs.items()
            }

            return functools.partial(func, *args, **kwargs)

        if "class" in config:
            # Handle instance method case
            instance = create_instance(config["class"])
            method_name = config.get("method", "__call__")
            method = getattr(instance, method_name)

            if not callable(method):
                raise CallableCreationError(
                    f"Attribute '{method_name}' is not callable"
                )

            return method

        # Handle direct callable case
        callable_obj = import_object(config)

        if not callable(callable_obj):
            raise CallableCreationError(
                f"Imported object '{callable_obj}' is not callable"
            )

        return callable_obj

    except ConfigError:
        raise
    except Exception as e:
        raise CallableCreationError(
            f"Failed to create callable: {str(e)}"
        ) from e
