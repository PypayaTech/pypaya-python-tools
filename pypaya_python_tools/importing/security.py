from dataclasses import dataclass, field
from typing import Set, Pattern, Union
from pathlib import Path
from pypaya_python_tools.importing.exceptions import ImportingSecurityError


@dataclass
class ImportSecurity:
    """Self-contained security for import operations."""

    # Basic controls
    enabled: bool = True
    max_depth: int = 10
    current_depth: int = 0

    # Import controls
    allow_file_imports: bool = False

    # Module security
    trusted_modules: Set[str] = field(default_factory=set)
    blocked_modules: Set[str] = field(default_factory=set)

    # Path security
    trusted_paths: Set[Union[str, Path, Pattern]] = field(default_factory=set)
    blocked_paths: Set[Union[str, Path, Pattern]] = field(default_factory=set)

    def __post_init__(self):
        """Normalize paths and validate settings."""
        self.trusted_paths = {
            Path(p) if isinstance(p, str) else p
            for p in self.trusted_paths
        }
        self.blocked_paths = {
            Path(p) if isinstance(p, str) else p
            for p in self.blocked_paths
        }

        if self.max_depth < 1:
            raise ValueError("max_depth must be positive")

    def validate_module(self, name: str) -> None:
        """Validate module import."""
        if not self.enabled:
            return

        if name in self.blocked_modules:
            raise ImportingSecurityError(f"Module {name} is blocked")

        if self.trusted_modules and name not in self.trusted_modules:
            raise ImportingSecurityError(f"Module {name} is not trusted")

    def validate_path(self, path: Path) -> None:
        """Validate file path."""
        if not self.enabled:
            return

        if not self.allow_file_imports:
            raise ImportingSecurityError("File imports are not allowed")

        path = Path(path)

        # Check blocked paths
        for blocked in self.blocked_paths:
            if isinstance(blocked, Pattern):
                if blocked.match(str(path)):
                    raise ImportingSecurityError(f"Path {path} matches blocked pattern")
            elif path.is_relative_to(blocked):
                raise ImportingSecurityError(f"Path {path} is in blocked path")

        # Must be in trusted paths if any are specified
        if self.trusted_paths:
            if not any(
                    path.is_relative_to(trusted) if isinstance(trusted, Path)
                    else bool(trusted.match(str(path)))
                    for trusted in self.trusted_paths
            ):
                raise ImportingSecurityError(f"Path {path} is not in trusted paths")

    def enter_level(self) -> None:
        """Enter new import depth level."""
        self.current_depth += 1
        if self.current_depth > self.max_depth:
            raise ImportingSecurityError(f"Maximum import depth ({self.max_depth}) exceeded")

    def exit_level(self) -> None:
        """Exit current import depth level."""
        self.current_depth = max(0, self.current_depth - 1)

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        pass
