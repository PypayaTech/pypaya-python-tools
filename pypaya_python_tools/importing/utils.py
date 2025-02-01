from typing import Any, Optional, Union, Dict, Type, TypeVar
from pathlib import Path
from pypaya_python_tools.importing.exceptions import ImportingError
from pypaya_python_tools.importing.manager import ImportManager
from pypaya_python_tools.importing.security import ImportSecurity
from pypaya_python_tools.importing.source import ImportSource, SourceType


T = TypeVar('T')


def import_module(name: str, security: Optional[ImportSecurity] = None) -> Any:
    """Convenience function to import a module."""
    manager = ImportManager(security)
    return manager.import_module(name)


def import_from_module(
        module: str,
        name: str,
        security: Optional[ImportSecurity] = None
) -> Any:
    """Convenience function to import from a module."""
    manager = ImportManager(security)
    return manager.import_from_module(module, name)


def import_from_file(
        path: Union[str, Path],
        name: Optional[str] = None,
        security: Optional[ImportSecurity] = None
) -> Any:
    """Convenience function to import from a file."""
    manager = ImportManager(security)
    return manager.import_from_file(path, name)


def import_builtin(name: str, security: Optional[ImportSecurity] = None) -> Any:
    """Convenience function to import builtin."""
    manager = ImportManager(security)
    return manager.import_builtin(name)


def import_class(
        module: str,
        class_name: str,
        base_class: Optional[Type[T]] = None,
        security: Optional[ImportSecurity] = None
) -> Type[T]:
    """
    Import a class with optional base class validation.

    Args:
        module: Module path
        class_name: Class name to import
        base_class: Optional base class to validate against
        security: Optional security settings

    Returns:
        Type[T]: Imported class
    """
    manager = ImportManager(security)
    cls = manager.import_from_module(module, class_name)

    if not isinstance(cls, type):
        raise ImportingError(f"{class_name} is not a class")

    if base_class and not issubclass(cls, base_class):
        raise ImportingError(f"{class_name} is not a subclass of {base_class.__name__}")

    return cls


def import_object(
        path_spec: Union[str, Path, Dict[str, str]],
        name: Optional[str] = None,
        security: Optional[ImportSecurity] = None
    ) -> Any:
    """
    Import an object using various path specification formats.

    Args:
        path_spec: Object location specified as:
            - module path ('myapp.models')
            - file path ('/path/to/module.py')
            - dict with 'path' and optional 'name' keys
            - full dotted path ('myapp.models.MyClass')
        name: Optional object name within module/file
        security: Optional security settings

    Returns:
        Imported object

    Raises:
        ImportError: Import failure
        ValueError: Invalid path specification

    Examples:
        # Separate path and name format
        obj1 = import_object('myapp.models', 'MyClass')
        obj2 = import_object('/path/to/module.py', 'MyClass')

        # Dictionary format
        obj3 = import_object({'path': 'myapp.models', 'name': 'MyClass'})

        # Full dotted path format
        obj4 = import_object('myapp.models.MyClass')
    """
    manager = ImportManager(security)

    # Handle dictionary format
    if isinstance(path_spec, dict):
        if "path" not in path_spec:
            raise ImportingError("Dictionary path_spec must contain 'path' key")
        name = path_spec.get("name", name)
        path_spec = path_spec["path"]

    path_str = str(path_spec)

    # Handle full dotted path format
    if (name is None and '.' in path_str and
            not path_str.endswith('.py') and
            not any(c in path_str for c in '/\\')):
        *module_parts, name = path_str.rsplit('.', 1)
        path_spec = '.'.join(module_parts)

    # Determine source type
    is_file = (isinstance(path_spec, Path) or
               any(c in path_str for c in '/\\') or
               path_str.endswith('.py'))

    source = ImportSource(
        type=SourceType.FILE if is_file else SourceType.MODULE,
        location=path_spec,
        name=name
    )

    return manager._resolve(source)
