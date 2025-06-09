import pytest
from pypaya_python_tools.execution import (
    PythonREPL, ExecutionResult,
    StringPatternAnalyzer, ImportAnalyzer, NameAccessAnalyzer, SecurityAnalyzerChain
)
from pypaya_python_tools.execution.exceptions import ExecutionError, ExecutionSecurityError


# === Basic REPL fixtures ===

@pytest.fixture
def basic_repl():
    """Basic REPL with no security analyzer"""
    return PythonREPL()


@pytest.fixture
def secure_repl():
    """REPL with a comprehensive security analyzer"""
    analyzer = SecurityAnalyzerChain([
        StringPatternAnalyzer(forbidden_patterns=["eval(", "exec(", "os.system"]),
        ImportAnalyzer(blocked_modules={"os", "subprocess"})
    ])
    return PythonREPL(security_analyzer=analyzer)


# === Basic REPL functionality tests ===

def test_simple_print(basic_repl):
    """Test basic print statement execution"""
    result = basic_repl.execute("print('Hello, world!')")
    assert str(result).strip() == "Hello, world!"
    assert result.stdout.strip() == "Hello, world!"
    assert not result.stderr
    assert not result.error


def test_multi_line_code(basic_repl):
    """Test multi-line code execution"""
    code = """
x = 10
print(2 * x)
    """
    result = basic_repl.execute(code)
    assert str(result).strip() == "20"
    assert basic_repl.locals['x'] == 10


def test_state_maintenance(basic_repl):
    """Test global state is maintained between executions"""
    basic_repl.execute("x = 10")
    basic_repl.execute("x += 5")
    result = basic_repl.execute("print(x)")
    assert str(result).strip() == "15"
    assert basic_repl.locals['x'] == 15


def test_complex_calculation(basic_repl):
    """Test complex calculation with recursion"""
    code = """
def factorial(n):
    if n == 0 or n == 1:
        return 1
    return n * factorial(n-1)

print(factorial(5))
    """
    result = basic_repl.execute(code)
    assert str(result).strip() == "120"
    assert "factorial" in basic_repl.locals


def test_import_and_use(basic_repl):
    """Test importing modules and using their functionality"""
    code = """
import math
print(math.pi)
    """
    result = basic_repl.execute(code)
    assert float(str(result).strip()) == pytest.approx(3.14159, 0.00001)
    assert "math" in basic_repl.locals


def test_multiple_prints(basic_repl):
    """Test capturing multiple print statements"""
    code = """
print("First line")
print("Second line")
print("Third line")
    """
    result = basic_repl.execute(code)
    assert str(result).strip().split('\n') == ["First line", "Second line", "Third line"]


def test_stderr_capture(basic_repl):
    """Test capturing stderr output"""
    code = """
import sys
print('error message', file=sys.stderr)
    """
    result = basic_repl.execute(code)
    assert result.stderr.strip() == "error message"
    assert not result.stdout


def test_complex_state_maintenance(basic_repl):
    """Test state maintenance with complex data structures"""
    basic_repl.execute("data = {'numbers': [], 'total': 0}")
    basic_repl.execute("for i in range(5): data['numbers'].append(i); data['total'] += i")
    result = basic_repl.eval("data")
    assert result.result == {'numbers': [0, 1, 2, 3, 4], 'total': 10}


def test_function_definition_and_call(basic_repl):
    """Test defining and calling functions"""
    basic_repl.execute("""
def greet(name):
    return f"Hello, {name}!"
""")
    result = basic_repl.eval('greet("Python")')
    assert result.result == "Hello, Python!"


# === Exception handling tests ===

def test_exception_handling(basic_repl):
    """Test basic exception handling"""
    result = basic_repl.execute("1 / 0")
    assert "ZeroDivisionError" in result.error
    assert not result.stdout


def test_syntax_error(basic_repl):
    """Test syntax error handling"""
    result = basic_repl.execute("if True print('wrong')")
    assert "SyntaxError" in result.error


def test_name_error(basic_repl):
    """Test name error handling"""
    result = basic_repl.execute("undefined_variable")
    assert "NameError" in result.error


def test_attribute_error(basic_repl):
    """Test attribute error handling"""
    result = basic_repl.execute("'string'.undefined_method()")
    assert "AttributeError" in result.error


# === Security analyzer tests ===

def test_repl_init_with_no_analyzer(basic_repl):
    """Test that REPL works without a security analyzer"""
    assert basic_repl.security_analyzer is None

    # Should execute any code without security checks
    result = basic_repl.execute("import os")
    assert result.error is None


def test_repl_with_analyzer(secure_repl):
    """Test that REPL with analyzer blocks unsafe code"""
    # Should block unsafe code
    with pytest.raises(ExecutionSecurityError):
        secure_repl.execute("import os")

    with pytest.raises(ExecutionSecurityError):
        secure_repl.execute("result = eval('2 + 2')")

    # Should allow safe code
    result = secure_repl.execute("x = 40 + 2")
    assert result.error is None
    assert result.security_violations == []


def test_skip_security_check(secure_repl):
    """Test bypassing security checks with skip_security_check flag"""
    # Should normally block this
    with pytest.raises(ExecutionSecurityError):
        secure_repl.execute("import os")

    # Should allow with skip_security_check
    result = secure_repl.execute("import os", skip_security_check=True)
    assert result.error is None


def test_security_analysis_without_execution(secure_repl):
    """Test analyzing code for security violations without executing it"""
    # Analyze without executing
    violations = secure_repl.analyze("import os; os.system('rm -rf /')")
    assert len(violations) >= 2  # Should catch both the import and os.system
    assert any("import" in v.lower() for v in violations)
    assert any("system" in v.lower() for v in violations)


def test_eval_with_security(secure_repl):
    """Test eval mode with security checks"""
    # Should block unsafe eval
    with pytest.raises(ExecutionSecurityError):
        secure_repl.eval("'eval()'")

    # Should allow safe eval
    result = secure_repl.eval("40 + 2")
    assert result.result == 42
    assert result.error is None


# === Custom analyzer tests ===

def test_string_pattern_analyzer_integration():
    """Test integration with StringPatternAnalyzer"""
    analyzer = StringPatternAnalyzer(
        forbidden_patterns=["eval(", "exec("],
        required_patterns=["# SAFE"]
    )
    repl = PythonREPL(security_analyzer=analyzer)

    # Missing required pattern
    with pytest.raises(ExecutionSecurityError):
        repl.execute("print('Hello')")

    # Has required pattern but forbidden pattern too
    with pytest.raises(ExecutionSecurityError):
        repl.execute("# SAFE\neval('2+2')")

    # Valid code with required pattern
    result = repl.execute("# SAFE\nprint('Hello')")
    assert result.stdout.strip() == "Hello"


def test_import_analyzer_integration():
    """Test integration with ImportAnalyzer"""
    analyzer = ImportAnalyzer(
        allowed_modules={"math", "random"},
        default_policy="deny"
    )
    repl = PythonREPL(security_analyzer=analyzer)

    # Allowed import
    result = repl.execute("import math; print(math.pi)")
    assert float(result.stdout.strip()) == pytest.approx(3.14159, 0.00001)

    # Blocked import
    with pytest.raises(ExecutionSecurityError):
        repl.execute("import os")


def test_name_analyzer_integration():
    """Test integration with NameAccessAnalyzer"""
    analyzer = NameAccessAnalyzer(
        allowed_names={"print", "len", "range", "sum"},
    )
    repl = PythonREPL(security_analyzer=analyzer)

    # Allowed names
    result = repl.execute("print(len(range(5)))")
    assert result.stdout.strip() == "5"

    # Blocked name
    with pytest.raises(ExecutionSecurityError):
        repl.execute("sorted([3, 1, 2])")


def test_chain_analyzer_integration():
    """Test integration with SecurityAnalyzerChain"""
    analyzer = SecurityAnalyzerChain([
        StringPatternAnalyzer(forbidden_patterns=["eval(", "exec("]),
        ImportAnalyzer(blocked_modules={"os", "subprocess"}),
        NameAccessAnalyzer(blocked_names={"__import__"})
    ])
    repl = PythonREPL(security_analyzer=analyzer)

    # Multiple violations
    with pytest.raises(ExecutionSecurityError) as excinfo:
        repl.execute("import os; eval('os.system(\"ls\")')")

    # Exception should contain information about all violations
    exc_message = str(excinfo.value)
    assert "import" in exc_message.lower()
    assert "eval" in exc_message.lower()


def test_execution_result_object(basic_repl):
    """Test properties of ExecutionResult object"""
    # Normal execution
    result = basic_repl.execute("""
print("stdout")
import sys
print("stderr", file=sys.stderr)
x = 42
""")

    assert result.stdout.strip() == "stdout"
    assert result.stderr.strip() == "stderr"
    assert result.error is None
    assert result.result is None
    assert result.security_violations == []

    # Execution with error
    result = basic_repl.execute("1/0")
    assert result.error is not None
    assert "ZeroDivisionError" in result.error

    # Eval result
    result = basic_repl.eval("40 + 2")
    assert result.result == 42
