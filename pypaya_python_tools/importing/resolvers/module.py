import importlib
import importlib.util
from pypaya_python_tools.importing.definitions import SourceType, ImportSource
from pypaya_python_tools.importing.exceptions import ResolverError
from pypaya_python_tools.importing.resolvers.base import ImportResolver, ResolveResult


class ModuleResolver(ImportResolver):
    """Handles importing from Python modules."""

    def can_handle(self, source: ImportSource) -> bool:
        return source.type == SourceType.MODULE

    def resolve(self, source: ImportSource) -> ResolveResult:
        try:
            module = importlib.import_module(str(source.location))

            if not source.name:
                return ResolveResult(module)

            if not hasattr(module, source.name):
                raise ResolverError(
                    f"Module '{source.location}' has no attribute '{source.name}'"
                )

            return ResolveResult(
                getattr(module, source.name),
                metadata={"module": module}
            )

        except ImportError as e:
            raise ResolverError(f"Failed to import module: {str(e)}")
