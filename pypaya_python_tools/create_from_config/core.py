from typing import Any, Union, Optional, List, Dict
import inspect
from pathlib import Path
import importlib
from pypaya_python_tools.create_from_config.exceptions import (
    ConfigError,
    ImportingError,
    ValidationError,
    InstantiationError
)
from pypaya_python_tools.create_from_config.types import ConfigDict


def create_instance(
        config: Union[ConfigDict, List[ConfigDict], Any],
        base_path: Optional[str] = None,
) -> Any:
    """
    Create instance(s) from configuration.

    Args:
        config: Configuration dictionary, list of configurations, or direct value.
            Dictionary must include one of:
            - 'module': str - module path (e.g., 'datetime')
            - 'file': str - file path
            May include:
            - 'class': str - class name (e.g., 'datetime')
            - 'args': list - positional arguments
            - 'kwargs': dict - keyword arguments
            - 'base_path': str - base path for imports
        base_path: Optional base path for imports

    Returns:
        Created object(s)

    Raises:
        ConfigError: Base class for all configuration-related errors
        ImportingError: When object import fails
        ValidationError: When configuration is invalid
        InstantiationError: When object instantiation fails
    """
    # Handle list of configurations
    if isinstance(config, list):
        return [create_instance(item, base_path) for item in config]

    # Handle non-dict values
    if not isinstance(config, dict):
        return config

    # Validate configuration
    _validate_config(config)

    try:
        # Extract configuration
        module_name = config.get("module")
        file_path = config.get("file")
        class_name = config.get("class")
        cfg_base_path = config.get("base_path", base_path)
        args = config.get("args", [])
        kwargs = config.get("kwargs", {})

        # Import object
        obj = _import_object(module_name, file_path, class_name, cfg_base_path)

        # Validate if class is abstract
        if inspect.isclass(obj) and inspect.isabstract(obj):
            raise InstantiationError(f"Cannot instantiate abstract class: {obj.__name__}")

        # Handle nested configurations
        args = [create_instance(arg, cfg_base_path) for arg in args]
        kwargs = {
            key: create_instance(value, cfg_base_path)
            for key, value in kwargs.items()
        }

        return obj(*args, **kwargs)

    except ConfigError:
        raise
    except Exception as e:
        raise InstantiationError(f"Failed to create instance: {str(e)}") from e


def create_callable(
        config: Union[ConfigDict, Any],
        base_path: Optional[str] = None,
) -> Any:
    """
    Create callable from configuration.
    Similar to create_instance but ensures result is callable.

    Args:
        config: Configuration dictionary or direct callable
        base_path: Optional base path for imports

    Returns:
        Callable object

    Raises:
        ConfigError: If result is not callable
    """
    result = create_instance(config, base_path)

    if not callable(result):
        raise ConfigError(f"Result is not callable: {result}")

    return result


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration dictionary."""
    if "args" in config and not isinstance(config["args"], list):
        raise ValidationError("'args' must be a list")
    if "kwargs" in config and not isinstance(config["kwargs"], dict):
        raise ValidationError("'kwargs' must be a dictionary")
    if "class" in config and not isinstance(config["class"], str):
        raise ValidationError("'class' must be a string")
    if not any(key in config for key in ["module", "file"]):
        raise ValidationError("Must provide either 'module' or 'file'")


def _import_object(
        module_name: Optional[str],
        file_path: Optional[str],
        class_name: Optional[str],
        base_path: Optional[str]
) -> Any:
    """Import object from module or file."""
    try:
        if file_path:
            # Handle file import
            file_path = Path(file_path)
            if base_path:
                file_path = Path(base_path) / file_path
            # Implementation of file import...
            raise NotImplementedError("File import not yet implemented")

        if module_name:
            # Handle module import
            module = importlib.import_module(module_name)
            return getattr(module, class_name) if class_name else module

        raise ImportError("Neither module nor file path provided")

    except Exception as e:
        raise ImportError(f"Failed to import object: {str(e)}") from e
