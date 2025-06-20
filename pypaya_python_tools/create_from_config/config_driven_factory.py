from typing import Dict, Any, TypeVar, Generic, Optional, Type, List, Union, get_type_hints
from abc import ABC, abstractmethod
from dataclasses import dataclass
import inspect
from pypaya_python_tools.create_from_config import create_instance


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
    - Parameter validation
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
        self._class_info_cache: Dict[str, ClassInfo] = {}

        self._initialize_type_mapping()
        self._initialize_special_handlers()
        self._validate_factory_setup()
        self._initialize_class_info()

    def _initialize_class_info(self) -> None:
        """Initialize parameter information for all mapped classes."""
        for class_name, module_path in self.type_mapping.items():
            try:
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                self._class_info_cache[class_name] = self._get_class_info(cls)
            except (ImportError, AttributeError) as e:
                raise FactoryConfigError(f"Failed to load class {class_name} from {module_path}: {str(e)}")

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

    def _validate_parameters(self, class_name: str, config: Dict[str, Any]) -> None:
        """Validate configuration parameters against class requirements."""
        if class_name not in self._class_info_cache:
            return  # Skip validation for unknown classes (custom implementations)

        class_info = self._class_info_cache[class_name]

        # Check for required parameters
        for name, param_info in class_info.parameters.items():
            if param_info.required and name not in config:
                raise FactoryConfigError(
                    f"Missing required parameter '{name}' for class '{class_name}'. "
                    f"{param_info.doc if param_info.doc else ''}"
                )

            # Validate type if value is provided
            if name in config and param_info.type_hint:
                value = config[name]

                # Skip type validation for complex type hints (Union, Tuple, etc.)
                if hasattr(param_info.type_hint, "__origin__"):
                    continue

                if not isinstance(value, param_info.type_hint):
                    try:
                        # Attempt type conversion for simple types
                        config[name] = param_info.type_hint(value)
                    except (ValueError, TypeError):
                        raise FactoryConfigError(
                            f"Invalid type for parameter '{name}' in class '{class_name}'. "
                            f"Expected {param_info.type_hint.__name__}, got {type(value).__name__}"
                        )

    def _add_default_values(self, class_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add default values for missing optional parameters."""
        if class_name not in self._class_info_cache:
            return config

        class_info = self._class_info_cache[class_name]
        config_with_defaults = config.copy()

        for name, param_info in class_info.parameters.items():
            if name not in config_with_defaults and not param_info.required:
                config_with_defaults[name] = param_info.default

        return config_with_defaults

    def build(self, config: Dict[str, Any]) -> T:
        """Build an instance based on configuration."""
        try:
            normalized = self._normalize_config(config)

            # Handle special cases first
            if normalized.class_name in self.special_handlers:
                return self._validate_instance(
                    self.special_handlers[normalized.class_name](normalized.kwargs)
                )

            # Validate parameters and add defaults
            self._validate_parameters(normalized.class_name, normalized.kwargs)
            normalized.kwargs = self._add_default_values(normalized.class_name, normalized.kwargs)

            # Handle custom implementations
            if normalized.module or normalized.file:
                if not self.allow_custom:
                    raise FactoryConfigError(
                        f"Custom implementations not allowed in {self.__class__.__name__}"
                    )
                return self._create_custom_implementation(normalized)

            # Handle built-in implementations
            if normalized.class_name not in self.type_mapping:
                available = list(self.type_mapping.keys())
                raise FactoryConfigError(
                    f"Unknown class: {normalized.class_name}. "
                    f"Available: {available}"
                )

            # Create instance using type mapping
            instance_config = {
                "module": self.type_mapping[normalized.class_name],
                "class": normalized.class_name,
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
            "class": config.class_name,
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
