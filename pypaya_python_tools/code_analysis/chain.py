from typing import List

from pypaya_python_tools.code_analysis.base import CodeSecurityAnalyzer, SecurityViolation


class SecurityAnalyzerChain(CodeSecurityAnalyzer):
    """
    Chains multiple analyzers together

    Allows composing security analyzers in sequence, providing
    a comprehensive suite of checks.
    """

    def __init__(self, analyzers):
        """
        Initialize with a list of analyzers

        Args:
            analyzers: List of security analyzers to apply in sequence
        """
        self.analyzers = analyzers

    def analyze(self, code: str) -> List[SecurityViolation]:
        """
        Run all analyzers and combine results

        Args:
            code: Python code as string

        Returns:
            Combined list of SecurityViolation objects
        """
        all_violations = []
        for analyzer in self.analyzers:
            all_violations.extend(analyzer.analyze(code))
        return all_violations
