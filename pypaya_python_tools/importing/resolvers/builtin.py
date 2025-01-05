import builtins
from typing import Dict, Any
from pypaya_python_tools.importing.definitions import SourceType, ImportSource
from pypaya_python_tools.importing.exceptions import ResolverError
from pypaya_python_tools.importing.resolvers.base import ImportResolver, ResolveResult


class BuiltinResolver(ImportResolver):
    """Handles importing from builtins."""

    def can_handle(self, source: ImportSource) -> bool:
        return source.type == SourceType.BUILTIN

    def resolve(self, source: ImportSource) -> ResolveResult:
        """
        Resolve a builtin by name.

        The location parameter is ignored for builtins as they are always
        imported from the builtins module.
        """
        if not source.name:
            raise ResolverError("Builtin name must be specified")

        if not hasattr(builtins, source.name):
            raise ResolverError(f"No builtin named '{source.name}'")

        metadata: Dict[str, Any] = {
            "builtin": True,
            "name": source.name,
            "module": builtins
        }

        return ResolveResult(
            getattr(builtins, source.name),
            metadata=metadata
        )
