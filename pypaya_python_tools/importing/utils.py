from typing import Any, Optional, Union, Dict
from pathlib import Path
from pypaya_python_tools.importing.definitions import SourceType, ImportSource
from pypaya_python_tools.importing.import_manager import ImportManager


def import_from_module(
    module_name: str,
    object_name: Optional[str] = None,
    unsafe: bool = False
) -> Any:
    """Convenience function to import from module."""
    source = ImportSource(
        type=SourceType.MODULE,
        location=module_name,
        name=object_name,
        unsafe=unsafe
    )
    return ImportManager().import_object(source)


def import_from_file(
    file_path: Union[str, Path],
    object_name: Optional[str] = None,
    unsafe: bool = False
) -> Any:
    """Convenience function to import from file."""
    source = ImportSource(
        type=SourceType.FILE,
        location=file_path,
        name=object_name,
        unsafe=unsafe
    )
    return ImportManager().import_object(source)


def import_builtin(name: str) -> Any:
    """Convenience function to import builtin."""
    source = ImportSource(
        type=SourceType.BUILTIN,
        name=name
    )
    return ImportManager().import_object(source)


def import_object(path_spec: Union[str, Path, Dict[str, str]], name: str | None = None) -> Any:
    """
    Import an object by providing either a module path, file path, or a specification dictionary.

    Args:
        path_spec: Specifies the object location in one of these formats:
            - module path (e.g., 'myapp.models')
            - file path (e.g., '/path/to/module.py')
            - dictionary with 'path' and optional 'name' keys
              (e.g., {'path': 'myapp.models', 'name': 'MyClass'})
            - full dotted path including object name
              (e.g., 'myapp.models.MyClass')
        name: Optional object name within module/file.
              Ignored if path_spec is a dictionary with 'name' key
              or if path_spec contains the object name.

    Returns:
        The imported object

    Raises:
        ImportError: If the object cannot be imported
        ValueError: If the path specification format is invalid

    Examples:
        # Separate path and name format
        obj1 = import_object('myapp.models', 'MyClass')
        obj2 = import_object('/path/to/module.py', 'MyClass')

        # Dictionary format
        obj3 = import_object({'path': 'myapp.models', 'name': 'MyClass'})

        # Full dotted path format
        obj4 = import_object('myapp.models.MyClass')
    """
    # Handle dictionary format
    if isinstance(path_spec, dict):
        if "path" not in path_spec:
            raise ValueError("Dictionary path_spec must contain 'path' key")
        name = path_spec.get("name", name)
        path_spec = path_spec["path"]
    else:
        path_spec = str(path_spec)

        # Handle full dotted path format if no explicit name provided
        if name is None and '.' in path_spec and not path_spec.endswith(".py"):
            *module_parts, name = path_spec.rsplit('.', 1)
            path_spec = '.'.join(module_parts)

    if isinstance(path_spec, Path) or ('/' in str(path_spec) or '\\' in str(path_spec)):
        source = ImportSource(type=SourceType.FILE, location=path_spec, name=name)
    else:
        source = ImportSource(type=SourceType.MODULE, location=path_spec, name=name)

    return ImportManager().import_object(source)
