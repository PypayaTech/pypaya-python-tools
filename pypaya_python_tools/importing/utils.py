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


def import_file(
        path: Union[str, Path],
        security: Optional[ImportSecurity] = None
) -> Any:
    """Convenience function to import from a file."""
    manager = ImportManager(security)
    return manager.import_file(path)


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
    return import_object("builtins", name, security)


def import_object(
        source: Union[str, Path, Dict[str, str]],
        object_name: Optional[str] = None,
        security: Optional[ImportSecurity] = None
    ) -> Any:
    """
    Import an object using various path specification formats.

    Args:
        source: Object location specified as:
            - module path ('myapp.models')
            - file path ('/path/to/module.py')
            - dict with 'path' and optional 'name' keys
        object_name: Optional object name within module/file
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
    """
    manager = ImportManager(security)

    # Handle dictionary format
    if isinstance(source, dict):
        if "path" not in source:
            raise ImportingError("Dictionary source must contain 'path' key")
        object_name = source.get("name", object_name)
        source = source["path"]

    path_str = str(source)

    # Determine source type
    is_file = (isinstance(source, Path) or
               any(c in path_str for c in '/\\') or
               path_str.endswith('.py'))

    source = ImportSource(
        type=SourceType.FILE if is_file else SourceType.MODULE,
        location=source,
        name=object_name
    )

    return manager._resolve(source)
