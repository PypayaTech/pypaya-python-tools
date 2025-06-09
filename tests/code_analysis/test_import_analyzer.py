import pytest
from pypaya_python_tools.code_analysis import ImportAnalyzer


class TestImportAnalyzer:

    def test_init_with_defaults(self):
        analyzer = ImportAnalyzer()
        assert analyzer.allowed_modules == set()
        assert analyzer.blocked_modules == set()
        assert analyzer.allow_import_from is True
        assert analyzer.default_policy == "deny"

    def test_invalid_default_policy(self):
        with pytest.raises(ValueError):
            ImportAnalyzer(default_policy="invalid")

    def test_empty_code_no_violations(self):
        analyzer = ImportAnalyzer()
        violations = analyzer.analyze("")
        assert len(violations) == 0
        assert analyzer.is_safe("")

    def test_syntax_error_reporting(self):
        analyzer = ImportAnalyzer()

        # Code with syntax error
        code = "import os\nfrom sys import\n"
        violations = analyzer.analyze(code)
        assert len(violations) == 1
        assert "Syntax error" in str(violations[0])

    def test_blocked_modules(self):
        analyzer = ImportAnalyzer(
            blocked_modules={"os", "subprocess", "sys"},
            default_policy="allow"
        )

        # Try importing blocked modules
        assert not analyzer.is_safe("import os")
        assert not analyzer.is_safe("import subprocess")
        assert not analyzer.is_safe("import sys")

        # Other modules should be allowed
        assert analyzer.is_safe("import math")
        assert analyzer.is_safe("import re")

        # Check from imports
        assert not analyzer.is_safe("from os import path")
        assert analyzer.is_safe("from math import sin")

    def test_allowed_modules(self):
        analyzer = ImportAnalyzer(
            allowed_modules={"math", "re", "datetime"},
            default_policy="deny"
        )

        # Try importing allowed modules
        assert analyzer.is_safe("import math")
        assert analyzer.is_safe("import re")

        # Other modules should be blocked
        assert not analyzer.is_safe("import os")
        assert not analyzer.is_safe("import sys")

        # Check from imports
        assert analyzer.is_safe("from math import sin")
        assert not analyzer.is_safe("from os import path")

    def test_disallow_import_from(self):
        analyzer = ImportAnalyzer(
            allowed_modules={"math", "re", "datetime"},
            allow_import_from=False,
            default_policy="deny"
        )

        # Regular imports should work
        assert analyzer.is_safe("import math")

        # From imports should be blocked
        assert not analyzer.is_safe("from math import sin")

    def test_multiple_imports(self):
        analyzer = ImportAnalyzer(
            allowed_modules={"math", "re"},
            blocked_modules={"os", "sys"},
            default_policy="deny"
        )

        code = """
import math
import re
import os  # This should be blocked
"""
        violations = analyzer.analyze(code)
        assert len(violations) == 1
        assert "os" in str(violations[0])

        code = """
import math
from re import match
from os import path  # This should be blocked
"""
        violations = analyzer.analyze(code)
        assert len(violations) == 1
        assert "os" in str(violations[0])

    def test_import_as(self):
        analyzer = ImportAnalyzer(
            blocked_modules={"os", "sys"},
            default_policy="allow"
        )

        # Import with alias
        assert not analyzer.is_safe("import os as operating_system")
        assert analyzer.is_safe("import math as m")

        # From import with alias
        assert not analyzer.is_safe("from os import path as file_path")
        assert analyzer.is_safe("from math import sin as sine")
