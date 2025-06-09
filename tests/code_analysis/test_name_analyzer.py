from pypaya_python_tools.code_analysis import NameAccessAnalyzer


class TestNameAccessAnalyzer:

    def test_init_with_defaults(self):
        analyzer = NameAccessAnalyzer()
        assert analyzer.allowed_names == set()
        assert analyzer.blocked_names == set()
        assert analyzer.check_attributes is True

    def test_empty_code_no_violations(self):
        analyzer = NameAccessAnalyzer()
        violations = analyzer.analyze("")
        assert len(violations) == 0
        assert analyzer.is_safe("")

    def test_syntax_error_reporting(self):
        analyzer = NameAccessAnalyzer()

        # Code with syntax error
        code = "x = 1\nprint(y\n"
        violations = analyzer.analyze(code)
        assert len(violations) == 1
        assert "Syntax error" in str(violations[0])

    def test_allowed_names(self):
        analyzer = NameAccessAnalyzer(
            allowed_names={"print", "len", "min", "max"}
        )

        # Using allowed names should work
        assert analyzer.is_safe("print('Hello')")
        assert analyzer.is_safe("x = len('test')")

        # Using other names should be blocked
        assert not analyzer.is_safe("sorted([3, 1, 2])")

        # Using defined names within the code should work
        assert analyzer.is_safe("""
x = 10
y = x + 5
print(y)
        """)

    def test_blocked_names(self):
        analyzer = NameAccessAnalyzer(
            blocked_names={"eval", "exec", "open", "__import__"}
        )

        # Using blocked names should fail
        assert not analyzer.is_safe("eval('2 + 2')")
        assert not analyzer.is_safe("result = exec('x = 10')")

        # Other names should work
        assert analyzer.is_safe("print('Hello')")
        assert analyzer.is_safe("x = len('test')")

    def test_attribute_checking(self):
        analyzer = NameAccessAnalyzer(check_attributes=True)

        # Dangerous attribute access should be blocked
        assert not analyzer.is_safe("import os; os.system('ls')")
        assert not analyzer.is_safe("import subprocess; subprocess.call(['ls'])")

        # Non-dangerous attribute access should be fine
        assert analyzer.is_safe("import math; x = math.sin(0.5)")

        # Check with attribute checking disabled
        analyzer = NameAccessAnalyzer(check_attributes=False)
        assert analyzer.is_safe("import os; os.system('ls')")

    def test_defined_names(self):
        analyzer = NameAccessAnalyzer(
            allowed_names={"print"}
        )

        # Variables defined in the code should be usable
        assert analyzer.is_safe("""
x = 10
y = x + 5
print(y)
        """)

        # Functions defined in the code should be usable
        assert analyzer.is_safe("""
def add(a, b):
    return a + b

result = add(10, 20)
print(result)
        """)

        # Classes defined in the code should be usable
        assert analyzer.is_safe("""
class Person:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hello, {self.name}"

p = Person("Alice")
print(p.greet())
        """)

    def test_dangerous_attribute_patterns(self):
        analyzer = NameAccessAnalyzer()

        # Check various dangerous attribute patterns
        assert not analyzer.is_safe("import os; os.system('ls')")
        assert not analyzer.is_safe("import os; os.popen('ls')")
        assert not analyzer.is_safe("import os; os.execve('/bin/sh', [], {})")
        assert not analyzer.is_safe("import subprocess; subprocess.call(['ls'])")
        assert not analyzer.is_safe("import subprocess; subprocess.Popen(['ls'])")
        assert not analyzer.is_safe("import sys; sys.modules['os'].system('ls')")

        # Other attributes should be fine
        assert analyzer.is_safe("import os; path = os.path.join('a', 'b')")
