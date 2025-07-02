from typing import Dict, Any, TypeVar, Generic, Optional, Type, List, Union, get_type_hints
from abc import ABC, abstractmethod
from dataclasses import dataclass
import inspect
from pypaya_python_tools.create_from_config import create_instance
from pypaya_python_tools.importing import import_object, ImportSecurity


T = TypeVar('T')


class FactoryConfigError(Exception):
    """
        Raised when factory configuration or object creation fails.

        This includes:
        - Missing required parameters
        - Invalid parameter types
        - Invalid component configurations
        - Component creation failures
    """
    pass


@dataclass
class ParameterInfo:
    """Information about a class parameter."""
    name: str
    type_hint: Optional[Type]
    required: bool
    default: Any
    doc: Optional[str] = None


@dataclass
class ClassInfo:
    """Information about a class and its parameters."""
    parameters: Dict[str, ParameterInfo]
    doc: Optional[str] = None


@dataclass
class FactoryConfig:
    """Configuration for factory instance creation."""
    class_name: str
    args: List[Any] = None
    kwargs: Dict[str, Any] = None
    module: Optional[str] = None
    file: Optional[str] = None


class ConfigDrivenFactory(ABC, Generic[T]):
    """Base factory for creating specialized types of objects.

    Primary purpose:
    - Provides convenient mappings for predefined framework classes to their module paths
    - Allows custom implementations through explicit module/file specifications

    Features:
    - Built-in type mappings for framework classes
    - Support for custom implementations via module path or file path
    - Special case handling
    - Parameter validation for both built-in and custom classes
    - Flexible configuration formats
    """

    def __init__(
            self,
            base_class: Optional[Type[T]] = None,
            allow_custom: bool = True
    ):
        self.base_class = base_class
        self.allow_custom = allow_custom
        self.type_mapping: Dict[str, str] = {}
        self.special_handlers: Dict[str, callable] = {}
        self._class_info_cache: Dict[str, Optional[ClassInfo]] = {}

        self._initialize_type_mapping()
        self._initialize_special_handlers()
        self._validate_factory_setup()

    def _get_class_from_config(self, config: FactoryConfig) -> Type:
        """Get class object from factory configuration."""
        if config.file:
            return import_object(config.file, config.class_name, ImportSecurity(allow_file_imports=True))
        elif config.module:
            return import_object(config.module, config.class_name)
        elif config.class_name in self.type_mapping:
            module_path = self.type_mapping[config.class_name]
            return import_object(module_path, config.class_name)
        else:
            available = list(self.type_mapping.keys())
            raise FactoryConfigError(
                f"Unknown class: {config.class_name}. Available: {available}"
            )

    def _get_cache_key(self, config: FactoryConfig) -> str:
        """Generate cache key for class info based on configuration."""
        if config.file:
            return f"file:{config.file}:{config.class_name}"
        elif config.module:
            return f"module:{config.module}:{config.class_name}"
        else:
            return f"builtin:{config.class_name}"

    def _ensure_class_info_loaded(self, config: FactoryConfig) -> None:
        """Ensure class information is loaded for the specified configuration.

        Raises FactoryConfigError if the class cannot be loaded.
        """
        cache_key = self._get_cache_key(config)

        # Skip if already in cache (including None values which indicate previous failures)
        if cache_key in self._class_info_cache:
            if self._class_info_cache[cache_key] is None:
                raise FactoryConfigError(f"Class '{config.class_name}' is not available")
            return

        # Try to load class information
        try:
            cls = self._get_class_from_config(config)
            self._class_info_cache[cache_key] = self._get_class_info(cls)
        except Exception as e:
            # Cache the failure and raise a clear error
            self._class_info_cache[cache_key] = None

            # Provide context-specific error messages
            if config.file:
                location = f"file '{config.file}'"
            elif config.module:
                location = f"module '{config.module}'"
            else:
                location = f"built-in mapping (module: {self.type_mapping.get(config.class_name, 'unknown')})"

            raise FactoryConfigError(
                f"Failed to load class '{config.class_name}' from {location}: {str(e)}"
            ) from e

    def _get_class_info(self, cls: Type) -> ClassInfo:
        """Extract parameter information from a class."""

        # Check if the class has its own __init__ method
        if cls.__init__ is object.__init__:
            # The class uses the default constructor, no parameters needed
            return ClassInfo(parameters={}, doc=cls.__doc__)

        # Continue with normal parameter extraction for classes with custom __init__
        signature = inspect.signature(cls.__init__)
        type_hints = get_type_hints(cls.__init__)
        parameters = {}

        for name, param in signature.parameters.items():
            if name == "self":
                continue

            # IMPORTANT: Skip variadic parameters (*args and **kwargs)
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            type_hint = type_hints.get(name)
            required = param.default == inspect.Parameter.empty
            default = None if required else param.default

            # Get parameter documentation from docstring if available
            doc = None
            if cls.__init__.__doc__:
                doc_lines = cls.__init__.__doc__.split('\n')
                for line in doc_lines:
                    if f':param {name}:' in line:
                        doc = line.split(f':param {name}:')[1].strip()
                        break

            parameters[name] = ParameterInfo(
                name=name,
                type_hint=type_hint,
                required=required,
                default=default,
                doc=doc
            )

        return ClassInfo(
            parameters=parameters,
            doc=cls.__doc__
        )

    def _validate_parameters(self, config: FactoryConfig, params: Dict[str, Any]) -> None:
        """Validate configuration parameters against class requirements."""
        # Ensure class info is loaded (will raise if unavailable)
        self._ensure_class_info_loaded(config)

        cache_key = self._get_cache_key(config)
        class_info = self._class_info_cache[cache_key]

        # Check for required parameters
        for name, param_info in class_info.parameters.items():
            if param_info.required and name not in params:
                raise FactoryConfigError(
                    f"Missing required parameter '{name}' for class '{config.class_name}'. "
                    f"{param_info.doc if param_info.doc else ''}"
                )

            # Validate type if value is provided
            if name in params and param_info.type_hint:
                value = params[name]

                # Skip type validation for complex type hints (Union, Tuple, etc.)
                if hasattr(param_info.type_hint, "__origin__"):
                    continue

                if not isinstance(value, param_info.type_hint):
                    try:
                        # Attempt type conversion for simple types
                        params[name] = param_info.type_hint(value)
                    except (ValueError, TypeError):
                        raise FactoryConfigError(
                            f"Invalid type for parameter '{name}' in class '{config.class_name}'. "
                            f"Expected {param_info.type_hint.__name__}, got {type(value).__name__}"
                        )

    def _add_default_values(self, config: FactoryConfig, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add default values for missing optional parameters."""
        # Ensure class info is loaded (will raise if unavailable)
        self._ensure_class_info_loaded(config)

        cache_key = self._get_cache_key(config)
        class_info = self._class_info_cache[cache_key]
        params_with_defaults = params.copy()

        for name, param_info in class_info.parameters.items():
            if name not in params_with_defaults and not param_info.required:
                params_with_defaults[name] = param_info.default

        return params_with_defaults

    def build(self, config: Dict[str, Any]) -> T:
        """Build an instance based on configuration."""
        try:
            normalized = self._normalize_config(config)

            # Handle special cases first
            if normalized.class_name in self.special_handlers:
                return self._validate_instance(
                    self.special_handlers[normalized.class_name](normalized.kwargs)
                )

            # Handle custom implementations
            if normalized.module or normalized.file:
                if not self.allow_custom:
                    raise FactoryConfigError(
                        f"Custom implementations not allowed in {self.__class__.__name__}"
                    )

                # Validate parameters and add defaults for custom classes
                self._validate_parameters(normalized, normalized.kwargs)
                normalized.kwargs = self._add_default_values(normalized, normalized.kwargs)

                return self._create_custom_implementation(normalized)

            # For built-in implementations, validate parameters and add defaults
            self._validate_parameters(normalized, normalized.kwargs)
            normalized.kwargs = self._add_default_values(normalized, normalized.kwargs)

            # Create instance using type mapping
            instance_config = {
                "module": self.type_mapping[normalized.class_name],
                "class_name": normalized.class_name,
                "args": normalized.args or [],
                "kwargs": normalized.kwargs or {}
            }

            instance = create_instance(instance_config)
            return self._validate_instance(instance)

        except Exception as e:
            error_msg = f"Factory creation failed: {str(e)}\nConfiguration: {config}"
            raise FactoryConfigError(error_msg) from e

    @abstractmethod
    def _initialize_type_mapping(self) -> None:
        """Initialize mapping between type names and module paths."""
        pass

    def _initialize_special_handlers(self) -> None:
        """Initialize special case handlers."""
        pass

    def _validate_factory_setup(self) -> None:
        """Validate factory configuration."""
        if not self.type_mapping:
            raise ValueError(
                f"Factory {self.__class__.__name__} must define at least one type mapping"
            )

    def _normalize_config(self, config: Dict[str, Any]) -> FactoryConfig:
        """Normalize different config formats into standard format."""
        config = config.copy()
        if "class_name" not in config:
            raise FactoryConfigError("Configuration must include 'class_name' field")

        class_name = config.pop("class_name")

        # Handle explicit args/kwargs format
        if "args" in config or "kwargs" in config:
            return FactoryConfig(
                class_name=class_name,
                args=config.pop("args", []),
                kwargs=config.pop("kwargs", {}),
                module=config.pop("module", None),
                file=config.pop("file", None)
            )

        # Handle flat format where remaining fields become kwargs
        module = config.pop("module", None)
        file = config.pop("file", None)

        return FactoryConfig(
            class_name=class_name,
            args=[],
            kwargs=config,
            module=module,
            file=file
        )

    def _create_custom_implementation(self, config: FactoryConfig) -> T:
        """Create instance from custom implementation."""
        instance_config = {
            "class_name": config.class_name,
            "args": config.args or [],
            "kwargs": config.kwargs or {}
        }

        if config.file:
            instance_config["file"] = config.file
        else:
            instance_config["module"] = config.module

        instance = create_instance(instance_config)
        return self._validate_instance(instance)

    def _validate_instance(self, instance: Any) -> T:
        """Validate created instance."""
        if self.base_class and not isinstance(instance, self.base_class):
            raise FactoryConfigError(
                f"Invalid type: expected {self.base_class.__name__}, "
                f"got {type(instance).__name__}"
            )
        return instance
