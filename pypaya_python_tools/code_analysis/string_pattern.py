import re
from typing import List, Optional

from pypaya_python_tools.code_analysis.base import CodeSecurityAnalyzer, SecurityViolation


class StringPatternAnalyzer(CodeSecurityAnalyzer):
    """
    Analyzes code for forbidden string patterns

    This is a simple but effective first-pass filter that can catch
    obvious security issues like calls to dangerous functions.
    """

    def __init__(self,
                 forbidden_patterns: Optional[List[str]] = None,
                 required_patterns: Optional[List[str]] = None,
                 use_regex: bool = False):
        """
        Initialize with patterns to check

        Args:
            forbidden_patterns: Strings or regex patterns that should not appear
            required_patterns: Strings or regex patterns that must appear
            use_regex: Whether to treat patterns as regex
        """
        self.forbidden_patterns = forbidden_patterns or []
        self.required_patterns = required_patterns or []
        self.use_regex = use_regex

        # Compile regex patterns if needed
        if use_regex:
            self.forbidden_compiled = [re.compile(p) for p in self.forbidden_patterns]
            self.required_compiled = [re.compile(p) for p in self.required_patterns]

    def analyze(self, code: str) -> List[SecurityViolation]:
        """
        Check code against forbidden and required patterns

        Args:
            code: Python code as string

        Returns:
            List of SecurityViolation objects
        """
        violations = []

        # Check for forbidden patterns
        if self.forbidden_patterns:
            if self.use_regex:
                for i, pattern in enumerate(self.forbidden_compiled):
                    if pattern.search(code):
                        violations.append(
                            SecurityViolation(
                                f"Forbidden pattern found: '{self.forbidden_patterns[i]}'"
                            )
                        )
            else:
                for pattern in self.forbidden_patterns:
                    if pattern in code:
                        # Try to get line number
                        line_number = self._find_pattern_line(code, pattern)
                        violations.append(
                            SecurityViolation(
                                f"Forbidden pattern found: '{pattern}'",
                                line=line_number
                            )
                        )

        # Check for required patterns
        if self.required_patterns:
            if self.use_regex:
                for i, pattern in enumerate(self.required_compiled):
                    if not pattern.search(code):
                        violations.append(
                            SecurityViolation(
                                f"Required pattern not found: '{self.required_patterns[i]}'"
                            )
                        )
            else:
                for pattern in self.required_patterns:
                    if pattern not in code:
                        violations.append(
                            SecurityViolation(
                                f"Required pattern not found: '{pattern}'"
                            )
                        )

        return violations

    def _find_pattern_line(self, code: str, pattern: str) -> Optional[int]:
        """
        Find the line number where a pattern appears

        Args:
            code: Python code
            pattern: String pattern to find

        Returns:
            Line number (1-based) or None if not found
        """
        lines = code.splitlines()
        for i, line in enumerate(lines, 1):
            if pattern in line:
                return i
        return None
