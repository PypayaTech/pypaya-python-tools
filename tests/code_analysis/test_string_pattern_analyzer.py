from pypaya_python_tools.code_analysis import StringPatternAnalyzer


class TestStringPatternAnalyzer:

    def test_init_with_defaults(self):
        analyzer = StringPatternAnalyzer()
        assert analyzer.forbidden_patterns == []
        assert analyzer.required_patterns == []
        assert analyzer.use_regex is False

    def test_empty_code_no_violations(self):
        analyzer = StringPatternAnalyzer(forbidden_patterns=["eval"])
        violations = analyzer.analyze("")
        assert len(violations) == 0
        assert analyzer.is_safe("")

    def test_forbidden_pattern_simple(self):
        analyzer = StringPatternAnalyzer(forbidden_patterns=["eval(", "exec("])

        # Code with forbidden patterns
        code = "result = eval('2 + 2')"
        violations = analyzer.analyze(code)
        assert len(violations) == 1
        assert "eval(" in str(violations[0])
        assert not analyzer.is_safe(code)

        # Code with multiple forbidden patterns
        code = "eval('x'); exec('y')"
        violations = analyzer.analyze(code)
        assert len(violations) == 2

        # Safe code
        code = "x = 1 + 2"
        assert analyzer.is_safe(code)

    def test_required_pattern_simple(self):
        analyzer = StringPatternAnalyzer(required_patterns=["# SAFE"])

        # Code without required pattern
        code = "x = 1 + 2"
        violations = analyzer.analyze(code)
        assert len(violations) == 1
        assert "required pattern" in str(violations[0]).lower()
        assert not analyzer.is_safe(code)

        # Code with required pattern
        code = "# SAFE\nx = 1 + 2"
        assert analyzer.is_safe(code)

    def test_regex_patterns(self):
        # Test regex forbidden patterns
        analyzer = StringPatternAnalyzer(
            forbidden_patterns=[r"eval\s*\(", r"exec\s*\("],
            use_regex=True
        )

        # Should catch patterns even with whitespace
        assert not analyzer.is_safe("eval (x)")
        assert not analyzer.is_safe("exec  ('code')")

        # Should not catch things like "evaluation"
        assert analyzer.is_safe("evaluation = True")

        # Test regex required patterns
        analyzer = StringPatternAnalyzer(
            required_patterns=[r"^def\s+test_"],
            use_regex=True
        )

        # Should require a function definition at the start
        assert not analyzer.is_safe("x = 1")
        assert analyzer.is_safe("def test_func():\n    pass")
        assert not analyzer.is_safe("# Comment\ndef test_func():\n    pass")

    def test_line_number_reporting(self):
        analyzer = StringPatternAnalyzer(forbidden_patterns=["eval("])

        code = """
x = 1
y = 2
result = eval('x + y')
z = 3
"""
        violations = analyzer.analyze(code)
        assert len(violations) == 1
        assert violations[0].line == 4  # Line number should be 4
