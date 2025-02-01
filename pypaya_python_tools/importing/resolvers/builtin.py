import builtins
from typing import Any
from pypaya_python_tools.importing.exceptions import ResolverError
from pypaya_python_tools.importing.resolvers.base import ImportResolver, ResolveResult
from pypaya_python_tools.importing.source import ImportSource, SourceType


class BuiltinResolver(ImportResolver):
    """Resolver for Python built-in objects."""

    def can_handle(self, source: ImportSource) -> bool:
        return source.type == SourceType.BUILTIN

    def _do_resolve(self, source: ImportSource) -> ResolveResult[Any]:
        if not source.name:
            raise ResolverError("Name must be specified for builtin resolution")

        try:
            value = getattr(builtins, source.name)
            return ResolveResult(
                value=value,
                metadata={"type": "builtin", "name": source.name}
            )
        except AttributeError as e:
            raise ResolverError(f"Builtin {source.name} not found") from e
