from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Union
from pypaya_python_tools.importing.exceptions import ImportingError


class SourceType(Enum):
    """Types of import sources."""
    MODULE = auto()
    FILE = auto()


@dataclass
class ImportSource:
    """Specification of where and what to import.

    Args:
        type (SourceType): Type of source
        location (Optional[Union[str, Path]]): Location
            - For MODULE: module path (e.g., "json", "os.path")
            - For FILE: file path
        name (Optional[str]):
            - For MODULE: attribute name to import from module (optional)
            - For FILE: attribute name to import from file (optional)
    """
    type: SourceType
    location: Optional[Union[str, Path]] = None
    name: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize the source."""
        # Handle file paths
        if self.type == SourceType.FILE and self.location:
            self.location = Path(self.location) if isinstance(self.location, str) else self.location

        if not self.location:
            raise ImportingError(f"location must be specified")

    @property
    def is_module(self) -> bool:
        return self.type == SourceType.MODULE

    @property
    def is_file(self) -> bool:
        return self.type == SourceType.FILE
