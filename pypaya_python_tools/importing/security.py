from dataclasses import dataclass
from typing import Optional, Union
from pathlib import Path


class SecurityError(Exception):
    """Raised when security constraints are violated during imports or object access."""
    pass


@dataclass
class SecurityContext:
    """Security settings for import and object access operations.

    Controls:
    - File imports (allow_file_imports, trusted_paths)
    - Dynamic object creation (allow_dynamic_creation)
    - Object modification (allow_modification)
    """
    allow_file_imports: bool = True
    allow_dynamic_creation: bool = True
    allow_modification: bool = True
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
DEFAULT_SECURITY = SecurityContext()
STRICT_SECURITY = SecurityContext(
    allow_file_imports=False,
    allow_dynamic_creation=False,
    allow_modification=False
)
