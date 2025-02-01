import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any
from pypaya_python_tools.importing.source import ImportSource, SourceType
from pypaya_python_tools.importing.exceptions import ResolverError
from pypaya_python_tools.importing.resolvers.base import ImportResolver, ResolveResult


class FileResolver(ImportResolver):
    """Resolver for Python files."""

    def can_handle(self, source: ImportSource) -> bool:
        return source.type == SourceType.FILE

    def _do_resolve(self, source: ImportSource) -> ResolveResult[Any]:
        if not source.location:
            raise ResolverError("File path must be specified")

        path = Path(source.location)

        # Validate path through security
        self.security.validate_path(path)

        try:
            # Generate a unique module name
            module_name = f"_dynamic_import_{path.stem}_{id(path)}"

            # Create module spec
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                raise ResolverError(f"Cannot load file {path}")

            # Create module
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module

            # Execute module
            spec.loader.exec_module(module)

            # If no specific name requested, return the module
            if not source.name:
                return ResolveResult(
                    value=module,
                    metadata={"type": "file_module", "path": str(path)}
                )

            # Get specific object from module
            try:
                value = getattr(module, source.name)
                return ResolveResult(
                    value=value,
                    metadata={
                        "type": "file_attribute",
                        "path": str(path),
                        "name": source.name
                    }
                )
            except AttributeError as e:
                raise ResolverError(
                    f"Object {source.name} not found in file {path}"
                ) from e

        except Exception as e:
            raise ResolverError(f"Failed to import from file {path}") from e
