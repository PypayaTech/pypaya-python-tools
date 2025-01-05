from typing import Any, Optional, Union
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


def import_object(path: Union[str, Path], name: Optional[str] = None) -> Any:
    """
    Import an object by providing either a module or a file path.

    Args:
        path: Either module path (e.g., 'myapp.models') or file path (e.g., '/path/to/module.py')
        name: Optional object name within module/file
    """
    if isinstance(path, Path) or ('/' in str(path) or '\\' in str(path)):
        source = ImportSource(type=SourceType.FILE, location=path, name=name)
    else:
        source = ImportSource(type=SourceType.MODULE, location=path, name=name)

    return ImportManager().import_object(source)
