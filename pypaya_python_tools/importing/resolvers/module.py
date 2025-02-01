import importlib
import importlib.util
from typing import Any
from pypaya_python_tools.importing.resolvers.base import ImportResolver, ResolveResult
from pypaya_python_tools.importing.source import ImportSource, SourceType
from pypaya_python_tools.importing.exceptions import ResolverError


class ModuleResolver(ImportResolver):
    """Resolver for Python modules."""

    def can_handle(self, source: ImportSource) -> bool:
        return source.type == SourceType.MODULE

    def _do_resolve(self, source: ImportSource) -> ResolveResult[Any]:
        if not source.location:
            raise ResolverError("Module path must be specified")

        try:
            # Validate module through security
            self.security.validate_module(str(source.location))

            # Import the module
            module = importlib.import_module(str(source.location))

            # If no specific name requested, return the module
            if not source.name:
                return ResolveResult(
                    value=module,
                    metadata={"type": "module", "name": source.location}
                )

            # Get specific object from module
            try:
                value = getattr(module, source.name)
                return ResolveResult(
                    value=value,
                    metadata={
                        "type": "module_attribute",
                        "module": source.location,
                        "name": source.name
                    }
                )
            except AttributeError as e:
                raise ResolverError(
                    f"Object {source.name} not found in module {source.location}"
                ) from e

        except ImportError as e:
            raise ResolverError(f"Failed to import module {source.location}") from e
