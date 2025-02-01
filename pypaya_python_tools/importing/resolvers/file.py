import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Any
from pypaya_python_tools.importing.definitions import SourceType, ImportSource
from pypaya_python_tools.importing.exceptions import ResolverError, ImportSecurityError
from pypaya_python_tools.importing.resolvers.base import ImportResolver, ResolveResult


class FileResolver(ImportResolver):
    """Handles importing from files."""

    def can_handle(self, source: ImportSource) -> bool:
        return source.type == SourceType.FILE

    def _validate_source(self, source: ImportSource) -> None:
        if not self.security.allow_file_imports:
            raise ImportSecurityError("File imports are not allowed")

        path = Path(source.location)
        if not self.security.is_safe_path(path):
            raise ImportSecurityError(f"Path {path} is not in trusted paths")

    def resolve(self, source: ImportSource) -> ResolveResult:
        self._validate_source(source)
        path = Path(source.location)

        if not path.exists():
            raise ResolverError(f"File not found: {path}")

        try:
            spec = importlib.util.spec_from_file_location(
                path.stem, str(path)
            )
            if spec is None or spec.loader is None:
                raise ResolverError(f"Cannot load spec from {path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Create metadata dictionary
            metadata: Dict[str, Any] = {
                "file_path": path,
                "module": module,
                "module_name": path.stem
            }

            if not source.name:
                return ResolveResult(module, metadata=metadata)

            if not hasattr(module, source.name):
                raise ResolverError(
                    f"Module from {path} has no attribute '{source.name}'"
                )

            return ResolveResult(
                getattr(module, source.name),
                metadata=metadata
            )

        except Exception as e:
            raise ResolverError(f"Failed to import from file: {str(e)}")
