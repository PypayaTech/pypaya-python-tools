from dataclasses import dataclass
from typing import List, Optional, Any


@dataclass
class SecurityViolation:
    """Represents a security violation found in code"""
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    node: Any = None

    def __str__(self) -> str:
        location = f" at line {self.line}" if self.line is not None else ""
        if self.column is not None and self.line is not None:
            location = f" at line {self.line}, column {self.column}"
        return f"{self.message}{location}"


class CodeSecurityAnalyzer:
    """Base class for all code security analyzers"""

    def analyze(self, code: str) -> List[SecurityViolation]:
        """
        Analyze code for security violations

        Args:
            code: Python code as string

        Returns:
            List of SecurityViolation objects (empty if no violations)
        """
        raise NotImplementedError("Subclasses must implement this method")

    def is_safe(self, code: str) -> bool:
        """
        Check if code passes this security check

        Args:
            code: Python code as string

        Returns:
            True if code is safe according to this analyzer
        """
        return len(self.analyze(code)) == 0
