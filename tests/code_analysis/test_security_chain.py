from pypaya_python_tools.code_analysis import (
    SecurityAnalyzerChain, StringPatternAnalyzer, ImportAnalyzer, NameAccessAnalyzer
)


class TestSecurityAnalyzerChain:

    def test_empty_chain_no_violations(self):
        chain = SecurityAnalyzerChain([])
        violations = chain.analyze("import os")  # Should normally be blocked
        assert len(violations) == 0
        assert chain.is_safe("import os")

    def test_single_analyzer_chain(self):
        # Create a chain with just the import analyzer
        # Add default_policy="allow" to allow imports not explicitly blocked
        chain = SecurityAnalyzerChain([
            ImportAnalyzer(
                blocked_modules={"os", "subprocess"},
                default_policy="allow"
            )
        ])

        # Should block os import
        assert not chain.is_safe("import os")

        # Should allow math import
        assert chain.is_safe("import math")

    def test_multiple_analyzer_chain(self):
        # Create a chain with multiple analyzers
        chain = SecurityAnalyzerChain([
            StringPatternAnalyzer(forbidden_patterns=["eval(", "exec("]),
            ImportAnalyzer(
                blocked_modules={"os", "subprocess"},
                default_policy="allow"
            ),
            NameAccessAnalyzer(blocked_names={"open", "__import__"})
        ])

        # Should catch string patterns
        assert not chain.is_safe("result = eval('2 + 2')")

        # Should catch import violations
        assert not chain.is_safe("import os")

        # Should catch name violations
        assert not chain.is_safe("f = open('file.txt')")

        # Safe code should pass all analyzers
        assert chain.is_safe("import math; x = math.sin(0.5)")

    def test_combined_violation_reporting(self):
        chain = SecurityAnalyzerChain([
            StringPatternAnalyzer(forbidden_patterns=["eval("]),
            ImportAnalyzer(blocked_modules={"os"})
        ])

        # Code with multiple violations
        code = """
import os
result = eval('os.system("ls")')
"""

        violations = chain.analyze(code)
        assert len(violations) == 2  # Should catch both issues

        # Check that violation messages are appropriate
        violation_texts = [str(v) for v in violations]
        assert any("import" in text.lower() for text in violation_texts)
        assert any("eval(" in text for text in violation_texts)
