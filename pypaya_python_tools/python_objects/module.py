from typing import Any, Dict, List, Optional, Set, Union, TypeVar, Type
from pathlib import Path
import inspect
import sys
from types import ModuleType
from dataclasses import dataclass, field

from pypaya_python_tools.importing.utils import import_object
from pypaya_python_tools.python_objects.base import PythonObject, ValidationError
from pypaya_python_tools.python_objects.function import Function
from pypaya_python_tools.python_objects.klass import PythonClass


M = TypeVar('M', bound=ModuleType)


class Module(PythonObject[M]):
    """
    Wrapper for Python modules with rich introspection capabilities.

    Features:
    - Module content analysis
    - Dependency tracking
    - Object importing
    - Package structure inspection
    """

    def __init__(self, obj: M) -> None:
        super().__init__(obj)
        self._content_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._dependency_cache: Optional[Dict[str, Set[str]]] = None
        # self._variables: Optional[Dict[str, Any]] = None

    def _validate_object(self, obj: Any) -> None:
        if not inspect.ismodule(obj):
            raise ValidationError(f"Expected module object, got {type(obj)}")

    # Properties
    @property
    def is_package(self) -> bool:
        """Check if module is a package."""
        return hasattr(self._obj, "__path__")

    @property
    def package_path(self) -> Optional[List[str]]:
        """Get package path if module is a package."""
        return getattr(self._obj, "__path__", None)

    @property
    def package_name(self) -> Optional[str]:
        """Get package name if this is a package."""
        return self.module.__package__ if self.is_package else None

    @property
    def is_builtin(self) -> bool:
        """Check if module is built-in."""
        return self._obj.__name__ in sys.builtin_module_names

    @property
    def parent_package(self) -> Optional[str]:
        """Get parent package name if module is part of a package."""
        name = self._obj.__name__
        if '.' in name:
            return name.rsplit('.', 1)[0]
        return None

    # Content analysis
    def get_content(self, include_private: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed information about module contents.

        Args:
            include_private: Whether to include private members

        Returns:
            Dictionary mapping names to content information
        """
        if self._content_cache is None:
            self._content_cache = {}
            for name, obj in inspect.getmembers(self._obj):
                if not include_private and name.startswith('_'):
                    continue

                info = {
                    "type": type(obj).__name__,
                    "is_callable": callable(obj),
                    "is_module": inspect.ismodule(obj),
                    "is_class": inspect.isclass(obj),
                    "is_function": inspect.isfunction(obj),
                    "module": getattr(obj, "__module__", None),
                    "doc": inspect.getdoc(obj)
                }

                if info["is_class"]:
                    info["bases"] = [base.__name__ for base in obj.__bases__]
                elif info["is_function"]:
                    info["signature"] = str(inspect.signature(obj))

                self._content_cache[name] = info

        return self._content_cache.copy()

    def get_classes(self, include_private: bool = False) -> Dict[str, PythonClass]:
        """Get all classes defined in the module."""
        return {
            name: PythonClass(obj)
            for name, obj in inspect.getmembers(self._obj, inspect.isclass)
            if (include_private or not name.startswith('_')) and
               obj.__module__ == self._obj.__name__
        }

    def get_functions(self, include_private: bool = False) -> Dict[str, Function]:
        """Get all functions defined in the module."""
        return {
            name: Function(obj)
            for name, obj in inspect.getmembers(self._obj, inspect.isfunction)
            if (include_private or not name.startswith('_')) and
               obj.__module__ == self._obj.__name__
        }

    def get_submodules(self) -> Dict[str, "Module"]:
        """Get all submodules if this is a package."""
        if not self.is_package:
            return {}

        return {
            name: Module(obj)
            for name, obj in inspect.getmembers(self._obj, inspect.ismodule)
            if obj.__name__.startswith(self._obj.__name__ + '.')
        }

    def get_dependencies(self) -> Dict[str, Set[str]]:
        """
        Get module dependencies based on imports.

        Returns:
            Dictionary mapping import types to sets of module names:
            - 'direct': Directly imported modules
            - 'conditional': Modules imported in try-except blocks
            - 'relative': Relative imports
            - 'from_imports': Specific names imported via 'from'
        """
        if self._dependency_cache is None:
            self._dependency_cache = {
                "direct": set(),
                "conditional": set(),
                "relative": set(),
                "from_imports": set()
            }

            source = self.get_source()
            if source:
                import ast
                try:
                    tree = ast.parse(source)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for name in node.names:
                                self._dependency_cache["direct"].add(name.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.level > 0:  # Relative import
                                self._dependency_cache["relative"].add(
                                    ('.' * node.level) + (node.module or '')
                                )
                            else:
                                self._dependency_cache["from_imports"].add(node.module)
                        elif isinstance(node, ast.Try):
                            for imp in [n for n in ast.walk(node)
                                        if isinstance(n, (ast.Import, ast.ImportFrom))]:
                                if isinstance(imp, ast.Import):
                                    for name in imp.names:
                                        self._dependency_cache["conditional"].add(name.name)
                                else:
                                    self._dependency_cache["conditional"].add(imp.module)
                except Exception:
                    pass  # Source parsing failed

        return self._dependency_cache.copy()

    # Object access
    def get_object(self, name: str) -> Any:
        """Get object from module by name."""
        if not hasattr(self._obj, name):
            raise AttributeError(f"Module has no attribute '{name}'")
        return getattr(self._obj, name)

    def get_class(self, name: str) -> PythonClass:
        """Get class from module by name."""
        obj = self.get_object(name)
        if not inspect.isclass(obj):
            raise ValueError(f"'{name}' is not a class")
        return PythonClass(obj)

    def get_function(self, name: str) -> Function:
        """Get function from module by name."""
        obj = self.get_object(name)
        if not inspect.isfunction(obj):
            raise ValueError(f"'{name}' is not a function")
        return Function(obj)

    # Creation methods
    @classmethod
    def from_name(cls, module_name: str) -> "Module":
        """Create module wrapper from module name."""
        try:
            module = __import__(module_name, fromlist=["__name__"])
            return cls(module)
        except ImportError as e:
            raise ValidationError(f"Failed to import module: {str(e)}")

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'Module':
        """Create module wrapper from file path."""
        try:
            module = import_object(file_path)
            return cls(module)
        except ImportError as e:
            raise ValidationError(f"Failed to import module: {str(e)}")

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'Module':
        """Create module from configuration dictionary."""
        if "type" not in config or "location" not in config:
            raise ValidationError("Config must specify type and location")

        if config["type"] == "module":
            return cls.from_name(config["location"])
        elif config["type"] == "file":
            return cls.from_file(config["location"])
        else:
            raise ValidationError(f"Unknown import type: {config['type']}")

    def to_config(self) -> Dict[str, Any]:
        """Convert module to configuration dictionary."""
        if self.is_builtin:
            config_type = "module"
            location = self._obj.__name__
        else:
            config_type = "file"
            location = str(self.file) if self.file else self._obj.__name__

        return {
            "type": config_type,
            "location": location,
            "is_package": self.is_package,
            "parent_package": self.parent_package
        }

    # Package operations
    def walk_packages(self) -> List[Dict[str, Any]]:
        """
        Walk through package and subpackages if module is a package.

        Returns:
            List of dictionaries containing:
            - name: Full module name
            - is_package: Whether item is a package
            - path: File path if not builtin
        """
        if not self.is_package:
            return []

        import pkgutil
        return [
            {
                "name": name,
                "is_package": ispkg,
                "path": str(Path(path)) if path else None
            }
            for finder, name, ispkg in pkgutil.walk_packages(
                self._obj.__path__,
                self._obj.__name__ + '.'
            )
        ]

    def get_all_members(self) -> Dict[str, Any]:
        """Get all public module members (use with caution on large modules)."""
        return {
            name: value
            for name, value in inspect.getmembers(self._obj)
            if not name.startswith('_')
        }

    def __getattr__(self, name: str) -> Any:
        """Support attribute access on module."""
        return self.get_object(name)



    # Old methods to analyze
    def _ensure_variables(self) -> None:
        """Ensure module variables are analyzed."""
        if self._variables is None:
            self._ensure_members()
            self._variables = {
                name: member.value
                for name, member in self._members.items()
                if member.type == "variable"
            }

    def get_variables(self, include_private: bool = False) -> Dict[str, Any]:
        """
        Get all module variables.

        Args:
            include_private: Whether to include private variables

        Returns:
            Dictionary mapping variable names to their values
        """
        self._ensure_variables()
        if include_private:
            return self._variables.copy()
        return {name: value for name, value in self._variables.items()
                if not name.startswith('_')}

    def get_all_names(self, include_private: bool = False) -> Set[str]:
        """
        Get all member names in the module.

        Args:
            include_private: Whether to include private names

        Returns:
            Set of member names
        """
        self._ensure_members()
        if include_private:
            return set(self._members.keys())
        return {name for name, member in self._members.items()
                if member.is_public}

    def to_dict(self) -> Dict[str, Any]:
        """Convert module representation to dictionary."""
        base_data = super().to_dict()

        self._ensure_members()

        module_data = {
            "is_package": self.is_package,
            "package_name": self.package_name,
            "members": {
                name: {
                    "name": member.name,
                    "type": member.type,
                    "is_public": member.is_public,
                    "docstring": member.docstring
                }
                for name, member in self._members.items()
            }
        }

        return {**base_data, **module_data}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Module":
        """
        Create module from dictionary representation.

        Args:
            data: Dictionary containing module path

        Returns:
            Module instance

        Raises:
            ValidationError: If data is invalid or module cannot be imported
        """
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary")

        if "module_path" not in data:
            raise ValidationError("Dictionary must contain 'module_path'")

        return cls(data["module_path"])

    # TODO
    # Add more module analysis capabilities?
    # Add support for more specific module types?
