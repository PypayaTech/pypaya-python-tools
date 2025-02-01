import functools
from typing import Any, Union, Optional, List, Dict, TypeVar, Type, Callable
import inspect
from pypaya_python_tools.create_from_config.exceptions import (
    ConfigError,
    ValidationError,
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
            Required keys:
            - 'class': str - class name
            - One of:
              - 'module': str - module path
              - 'file': str - file path

            Optional keys:
            - 'args': list - positional arguments for constructor
            - 'kwargs': dict - keyword arguments for constructor

        expected_type: Optional type to validate against
        security: Optional import security settings. By default:
            - File imports are allowed
            - All other security settings at their defaults

    Returns:
        Created instance(s)

    Raises:
        ValidationError: If configuration is invalid
        InstantiationError: If instance creation fails
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
        # Validate required keys
        if "class" not in config:
            raise ValidationError("Configuration must include 'class' key")
        if "module" not in config and "file" not in config:
            raise ValidationError("Must provide either 'module' or 'file'")

        # Validate args and kwargs
        if not isinstance(config.get("args", []), (list, tuple)):
            raise ValidationError("'args' must be a list or tuple")
        if not isinstance(config.get("kwargs", {}), dict):
            raise ValidationError("'kwargs' must be a dictionary")

        # Import the class
        if "file" in config:
            cls = import_object(config["file"], config["class"], security=security)
        else:
            cls = import_object(config["module"], config["class"], security=security)

        # Validate it's a class
        if not isinstance(cls, type):
            raise InstantiationError(f"'{config['class']}' is not a class")

        # Check if abstract
        if inspect.isabstract(cls):
            raise InstantiationError(f"Cannot instantiate abstract class: {cls.__name__}")

        # Process arguments recursively
        args = []
        for arg in config.get("args", []):
            if isinstance(arg, dict):
                args.append(create_instance(arg, None, security))
            elif isinstance(arg, list):
                args.append([
                    create_instance(item, None, security) if isinstance(item, dict) else item
                    for item in arg
                ])
            else:
                args.append(arg)

        kwargs = {}
        for key, value in config.get("kwargs", {}).items():
            if isinstance(value, dict):
                kwargs[key] = create_instance(value, None, security)
            elif isinstance(value, list):
                kwargs[key] = [
                    create_instance(item, None, security) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                kwargs[key] = value

        # Create instance
        instance = cls(*args, **kwargs)

        # Validate type if needed
        if expected_type and not isinstance(instance, expected_type):
            raise ValidationError(
                f"Created instance is of type {type(instance)}, expected {expected_type}"
            )

        return instance

    except (ConfigError, ValidationError, InstantiationError):
        raise
    except Exception as e:
        raise InstantiationError(f"Failed to create instance: {str(e)}") from e


def create_callable(
    config: Dict[str, Any],
    security: Optional[ImportSecurity] = None
) -> Callable:
    """
    Create a callable object from configuration.

    Supports three main cases:
    1. Direct callable import (function, built-in, etc.)
    2. Instance method (including classes with __call__)
    3. Partial function

    Args:
        config: Configuration dictionary
        security: Optional import security settings

    Returns:
        Callable object

    Raises:
        ConfigError: If configuration is invalid
        CallableCreationError: If callable creation fails
    """
    if security is None:
        security = ImportSecurity(allow_file_imports=True)

    try:
        # Case 1: Direct callable (module or file)
        if ("module" in config and "name" in config) or ("file" in config and "name" in config):
            source = config.get("module", config.get("file"))
            name = config["name"]
            obj = import_object(source, name, security=security)

            if not callable(obj):
                raise CallableCreationError(f"Imported object '{obj}' is not callable")

            return obj

        # Case 2: Class instance or method
        elif "class" in config:
            # Create the instance
            instance = create_instance(config["class"], security=security)

            # Get method if specified, otherwise use instance directly
            if "method" in config:
                method_name = config["method"]
                if not hasattr(instance, method_name):
                    raise CallableCreationError(
                        f"Instance has no attribute '{method_name}'"
                    )

                method = getattr(instance, method_name)
                if not callable(method):
                    raise CallableCreationError(
                        f"Attribute '{method_name}' is not callable"
                    )

                return method

            # Otherwise, instance itself should be callable
            if not callable(instance):
                raise CallableCreationError(
                    f"Instance of {type(instance).__name__} is not callable"
                )

            return instance

        # Case 3: Partial function
        elif "partial" in config:
            # Get the base function
            if not isinstance(config["partial"], dict) or "function" not in config["partial"]:
                raise ValidationError(
                    "Partial configuration must contain 'function' key with callable config"
                )

            # Create the base callable
            base_func = create_callable(config["partial"]["function"], security=security)

            # Process args and kwargs
            args = config["partial"].get("args", [])
            kwargs = config["partial"].get("kwargs", {})

            # Process nested configurations in args/kwargs
            processed_args = []
            for arg in args:
                if isinstance(arg, dict):
                    processed_args.append(create_instance(arg, None, security))
                elif isinstance(arg, list):
                    processed_args.append([
                        create_instance(item, None, security) if isinstance(item, dict) else item
                        for item in arg
                    ])
                else:
                    processed_args.append(arg)

            processed_kwargs = {}
            for key, value in kwargs.items():
                if isinstance(value, dict):
                    processed_kwargs[key] = create_instance(value, None, security)
                elif isinstance(value, list):
                    processed_kwargs[key] = [
                        create_instance(item, None, security) if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    processed_kwargs[key] = value

            # Create partial function
            return functools.partial(base_func, *processed_args, **processed_kwargs)

        else:
            raise ValidationError(
                "Invalid callable configuration: must include 'module'+'name', 'file'+'name', "
                "'class', or 'partial'"
            )

    except ConfigError:
        raise
    except Exception as e:
        raise CallableCreationError(f"Failed to create callable: {str(e)}") from e
