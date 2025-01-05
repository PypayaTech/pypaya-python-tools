from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Union


class SourceType(Enum):
    """Types of sources from which objects can be imported."""
    MODULE = auto()
    FILE = auto()
    BUILTIN = auto()
    PACKAGE = auto()


@dataclass
class ImportSource:
    """Specification of where and what to import.

    Args:
        type (SourceType): Type of source (MODULE, FILE, BUILTIN)
        location (Optional[Union[str, Path]]): Location for non-builtin imports
            - For MODULE: module path (e.g., "json", "os.path")
            - For FILE: file path
            - For BUILTIN: ignored/not needed
        name (Optional[str]):
            - For MODULE: attribute name to import from module (optional)
            - For FILE: attribute name to import from file (optional)
            - For BUILTIN: name of builtin (required)
        unsafe (bool): Flag for potentially unsafe operations
    """
    type: SourceType
    location: Optional[Union[str, Path]] = None
    name: Optional[str] = None
    unsafe: bool = False

    def __post_init__(self):
        """Validate and normalize the source specification."""
        # Handle file paths
        if self.type == SourceType.FILE and self.location:
            self.location = Path(self.location) if isinstance(self.location, str) else self.location

        # Validation
        if self.type == SourceType.BUILTIN:
            if not self.name:
                raise ValueError("name must be specified for BUILTIN source type")
            if self.location:
                raise ValueError("location should not be specified for BUILTIN source type")
        else:
            if not self.location:
                raise ValueError(f"location must be specified for {self.type.name} source type")
