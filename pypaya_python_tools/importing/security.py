from dataclasses import dataclass
from typing import Optional, Union
from pathlib import Path


@dataclass
class ImportSecurityContext:
    """Security settings for import operations."""
    allow_file_imports: bool = True
    trusted_paths: Optional[list[Path]] = None

    def __post_init__(self):
        if self.trusted_paths:
            self.trusted_paths = [
                Path(p) if isinstance(p, str) else p
                for p in self.trusted_paths
            ]

    def is_safe_path(self, path: Union[str, Path]) -> bool:
        if not self.allow_file_imports:
            return False

        path = Path(path) if isinstance(path, str) else path
        if not self.trusted_paths:
            return True

        return any(
            path.is_relative_to(trusted)
            for trusted in self.trusted_paths
        )


# Common configurations
DEFAULT_IMPORT_SECURITY = ImportSecurityContext()
STRICT_IMPORT_SECURITY = ImportSecurityContext(
    allow_file_imports=False
)
