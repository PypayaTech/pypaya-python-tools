import pytest
from pypaya_python_tools import PythonREPL


@pytest.fixture
def python_repl():
    return PythonREPL()


def test_simple_print(python_repl):
    output = python_repl.run("print('Hello, world!')")
    assert output.strip() == "Hello, world!"


def test_multi_line_code(python_repl):
    code = """
x = 10
print(2 * x)
    """
    output = python_repl.run(code)
    assert output.strip() == "20"


def test_state_maintenance(python_repl):
    python_repl.run("x = 10")
    python_repl.run("x += 5")
    output = python_repl.run("print(x)")
    assert output.strip() == "15"


def test_exception_handling(python_repl):
    output = python_repl.run("1 / 0")
    assert "ZeroDivisionError" in output


def test_timeout(python_repl):
    code = """
import time
time.sleep(5)
print('Finished sleeping')
    """
    output = python_repl.run(code, timeout=2)
    assert output == "Execution timed out"


def test_no_timeout(python_repl):
    code = """
import time
time.sleep(1)
print('Finished sleeping')
    """
    output = python_repl.run(code, timeout=2)
    assert output.strip() == "Finished sleeping"


def test_complex_calculation(python_repl):
    code = """
def factorial(n):
    if n == 0 or n == 1:
        return 1
    return n * factorial(n-1)

print(factorial(5))
    """
    output = python_repl.run(code)
    assert output.strip() == "120"


def test_import_and_use(python_repl):
    code = """
import math
print(math.pi)
    """
    output = python_repl.run(code)
    assert float(output.strip()) == pytest.approx(3.14159, 0.00001)


def test_multiple_prints(python_repl):
    code = """
print("First line")
print("Second line")
print("Third line")
    """
    output = python_repl.run(code)
    assert output.strip().split('\n') == ["First line", "Second line", "Third line"]
