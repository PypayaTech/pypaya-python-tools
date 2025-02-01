from typing import Any, Dict, Type, Optional
from pathlib import Path
from pypaya_python_tools.importing.security import ImportSecurity
from pypaya_python_tools.importing.source import ImportSource, SourceType
from pypaya_python_tools.importing.exceptions import ImportingError, ResolverError
from pypaya_python_tools.importing.resolvers.base import ImportResolver
from pypaya_python_tools.importing.resolvers.builtin import BuiltinResolver
from pypaya_python_tools.importing.resolvers.file import FileResolver
from pypaya_python_tools.importing.resolvers.module import ModuleResolver


class ImportManager:
    """Central manager for import operations."""

    def __init__(self, security: Optional[ImportSecurity] = None):
        self.security = security or ImportSecurity()
        self.resolvers: Dict[SourceType, ImportResolver] = {}

        # Register default resolvers
        self.register_resolver(SourceType.BUILTIN, BuiltinResolver(self.security))
        self.register_resolver(SourceType.FILE, FileResolver(self.security))
        self.register_resolver(SourceType.MODULE, ModuleResolver(self.security))

    def register_resolver(self, source_type: SourceType, resolver: ImportResolver) -> None:
        """Register a resolver for a source type."""
        self.resolvers[source_type] = resolver

    def import_module(self, name: str) -> Any:
        """Import an entire module."""
        return self._resolve(ImportSource(
            type=SourceType.MODULE,
            location=name
        ))

    def import_from_module(self, module: str, name: str) -> Any:
        """Import a specific object from a module."""
        return self._resolve(ImportSource(
            type=SourceType.MODULE,
            location=module,
            name=name
        ))

    def import_from_file(self, path: Path, name: Optional[str] = None) -> Any:
        """Import from a Python file."""
        return self._resolve(ImportSource(
            type=SourceType.FILE,
            location=path,
            name=name
        ))

    def import_builtin(self, name: str) -> Any:
        """Import a builtin object."""
        return self._resolve(ImportSource(
            type=SourceType.BUILTIN,
            name=name
        ))

    def _resolve(self, source: ImportSource) -> Any:
        """Resolve an import source using appropriate resolver."""
        resolver = self.resolvers.get(source.type)
        if not resolver:
            raise ImportingError(f"No resolver found for source type {source.type}")

        if not resolver.can_handle(source):
            raise ImportingError(f"Resolver cannot handle source {source}")

        try:
            result = resolver.resolve(source)
            return result.value
        except ResolverError as e:
            raise ImportingError(f"Import failed: {str(e)}") from e

    def validate_abstract(self, cls: Type) -> None:
        """Validate that a class is not abstract."""
        import inspect
        if inspect.isabstract(cls):
            raise ImportingError(f"Cannot use abstract class: {cls.__name__}")
