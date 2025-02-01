import pytest
from pypaya_python_tools.execution import PythonREPL
from pypaya_python_tools.execution.exceptions import ExecutionSecurityError
from pypaya_python_tools.execution.security import ExecutionSecurity


@pytest.fixture
def python_repl():
    return PythonREPL()


@pytest.fixture
def python_repl_with_eval():
    security = ExecutionSecurity(allow_eval=True)
    return PythonREPL(security=security)


def test_simple_print(python_repl):
    result = python_repl.execute("print('Hello, world!')")
    assert str(result).strip() == "Hello, world!"
    assert result.stdout.strip() == "Hello, world!"
    assert not result.stderr
    assert not result.error


def test_multi_line_code(python_repl):
    code = """
x = 10
print(2 * x)
    """
    result = python_repl.execute(code)
    assert str(result).strip() == "20"
    assert python_repl.locals['x'] == 10


def test_state_maintenance(python_repl):
    python_repl.execute("x = 10")
    python_repl.execute("x += 5")
    result = python_repl.execute("print(x)")
    assert str(result).strip() == "15"
    assert python_repl.locals['x'] == 15


def test_exception_handling(python_repl):
    result = python_repl.execute("1 / 0")
    assert "ZeroDivisionError" in result.error
    assert not result.stdout


def test_complex_calculation(python_repl):
    code = """
def factorial(n):
    if n == 0 or n == 1:
        return 1
    return n * factorial(n-1)

print(factorial(5))
    """
    result = python_repl.execute(code)
    assert str(result).strip() == "120"
    assert "factorial" in python_repl.locals


def test_import_and_use(python_repl):
    code = """
import math
print(math.pi)
    """
    result = python_repl.execute(code)
    assert float(str(result).strip()) == pytest.approx(3.14159, 0.00001)
    assert "math" in python_repl.locals


def test_multiple_prints(python_repl):
    code = """
print("First line")
print("Second line")
print("Third line")
    """
    result = python_repl.execute(code)
    assert str(result).strip().split('\n') == ["First line", "Second line", "Third line"]


def test_eval_mode(python_repl_with_eval):
    result = python_repl_with_eval.eval("2 + 2")
    assert result.result == 4
    assert not result.stdout


def test_eval_not_allowed(python_repl):
    with pytest.raises(ExecutionSecurityError):
        python_repl.eval("2 + 2")


def test_stderr_capture(python_repl):
    code = """
import sys
print('error message', file=sys.stderr)
    """
    result = python_repl.execute(code)
    assert result.stderr.strip() == "error message"
    assert not result.stdout


def test_complex_state_maintenance(python_repl_with_eval):
    # Test with more complex data structures
    python_repl_with_eval.execute("data = {'numbers': [], 'total': 0}")
    python_repl_with_eval.execute("for i in range(5): data['numbers'].append(i); data['total'] += i")
    result = python_repl_with_eval.eval("data")
    assert result.result == {'numbers': [0, 1, 2, 3, 4], 'total': 10}


def test_function_definition_and_call(python_repl_with_eval):
    python_repl_with_eval.execute("""
def greet(name):
    return f"Hello, {name}!"
""")
    result = python_repl_with_eval.eval('greet("Python")')
    assert result.result == "Hello, Python!"


def test_syntax_error(python_repl):
    result = python_repl.execute("if True print('wrong')")
    assert "SyntaxError" in result.error


def test_name_error(python_repl):
    result = python_repl.execute("undefined_variable")
    assert "NameError" in result.error


def test_attribute_error(python_repl):
    result = python_repl.execute("'string'.undefined_method()")
    assert "AttributeError" in result.error
