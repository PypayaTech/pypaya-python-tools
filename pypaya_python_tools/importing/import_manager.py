from typing import Dict, Any
from pypaya_python_tools.importing.definitions import SourceType, ImportSource
from pypaya_python_tools.importing.security import ImportSecurityContext, DEFAULT_IMPORT_SECURITY
from pypaya_python_tools.importing.exceptions import ResolverError
from pypaya_python_tools.importing.resolvers.base import ImportResolver
from pypaya_python_tools.importing.resolvers.builtin import BuiltinResolver
from pypaya_python_tools.importing.resolvers.file import FileResolver
from pypaya_python_tools.importing.resolvers.module import ModuleResolver


class ImportManager:
    """Central manager for import operations."""

    def __init__(self, security_context: ImportSecurityContext = DEFAULT_IMPORT_SECURITY):
        self.security = security_context
        self.resolvers: Dict[SourceType, ImportResolver] = {}
        self._register_default_resolvers()

    def _register_default_resolvers(self) -> None:
        """Register default resolvers."""
        self.register_resolver(SourceType.MODULE, ModuleResolver(self.security))
        self.register_resolver(SourceType.FILE, FileResolver(self.security))
        self.register_resolver(SourceType.BUILTIN, BuiltinResolver(self.security))

    def register_resolver(self, source_type: SourceType, resolver: ImportResolver) -> None:
        """Register a new resolver."""
        self.resolvers[source_type] = resolver

    def import_object(self, source: ImportSource) -> Any:
        """Import object from specified source."""
        resolver = self.resolvers.get(source.type)
        if not resolver:
            raise ResolverError(f"No resolver for source type: {source.type}")

        if not resolver.can_handle(source):
            raise ResolverError(
                f"Resolver for {source.type} cannot handle this source"
            )

        result = resolver.resolve(source)
        return result.value
