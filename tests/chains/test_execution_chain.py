import types
import pytest
from pypaya_python_tools.chains.execution import ExecutionChain
from pypaya_python_tools.chains.base.state import ChainState
from pypaya_python_tools.execution.exceptions import ExecutionError, ExecutionSecurityError
from pypaya_python_tools.execution.security import ExecutionSecurity


@pytest.fixture
def permissive_security():
    """Security config that allows all operations"""
    return ExecutionSecurity(
        allow_eval=True,
        allow_exec=True,
        allow_compile=True,
        allow_subprocess=True,
        allowed_modules={'json', 'os', 'sys'},
        allowed_builtins={'print', 'len', 'str', 'int'}
    )


@pytest.fixture
def restricted_security():
    """Security config that restricts most operations"""
    return ExecutionSecurity(
        allow_eval=False,
        allow_exec=False,
        allow_compile=False,
        allow_subprocess=False,
        blocked_modules={'os', 'sys', 'subprocess'}
    )


@pytest.fixture
def permissive_chain(permissive_security):
    return ExecutionChain(security=permissive_security)


@pytest.fixture
def restricted_chain(restricted_security):
    return ExecutionChain(security=restricted_security)


# Tests with permissive security
def test_execute_code(permissive_chain):
    result = permissive_chain.execute_code("_value = 42")
    assert result.value == 42


def test_eval_expression(permissive_chain):
    result = permissive_chain.eval_expression("2 + 2")
    assert result.value == 4


def test_compile_code(permissive_chain):
    result = permissive_chain.compile_code("x = 1")
    assert result.value is not None
    assert isinstance(result.value, types.CodeType)  # Check if it's a code object

    # Optionally, verify the compiled code works
    namespace = {}
    exec(result.value, namespace)
    assert namespace['x'] == 1


def test_with_globals(permissive_chain):
    permissive_chain.with_globals({"x": 10})
    result = permissive_chain.eval_expression("x")
    assert result.value == 10


def test_with_locals(permissive_chain):
    permissive_chain.with_locals({"y": 20})
    result = permissive_chain.eval_expression("y")
    assert result.value == 20


def test_output_capture(permissive_chain):
    permissive_chain.execute_code("print('test')")
    assert permissive_chain.output.strip() == "test"


# Tests with restricted security
def test_eval_denied(restricted_chain):
    with pytest.raises(ExecutionSecurityError) as exc_info:
        restricted_chain.eval_expression("2 + 2")
    assert "eval() is not allowed" in str(exc_info.value)


def test_compile_denied(restricted_chain):
    with pytest.raises(ExecutionSecurityError) as exc_info:
        restricted_chain.compile_code("x = 1")
    assert "compile() is not allowed" in str(exc_info.value)


def test_subprocess_denied(restricted_chain):
    with pytest.raises(ExecutionSecurityError) as exc_info:
        restricted_chain.execute_code("import subprocess")
    assert "subprocess usage is not allowed" in str(exc_info.value)


# Error handling tests
def test_syntax_error(permissive_chain):
    with pytest.raises(ExecutionError) as exc_info:
        permissive_chain.execute_code("invalid python code")
    assert "SyntaxError" in str(exc_info.value)


def test_runtime_error(permissive_chain):
    with pytest.raises(ExecutionError) as exc_info:
        permissive_chain.execute_code("1/0")
    assert "ZeroDivisionError" in str(exc_info.value)


def test_undefined_variable(permissive_chain):
    with pytest.raises(ExecutionError) as exc_info:
        permissive_chain.execute_code("undefined_variable")
    assert "NameError" in str(exc_info.value)


# State and context tests
def test_chain_state_transitions(permissive_chain):
    assert permissive_chain.state == ChainState.INITIAL

    permissive_chain.execute_code("_value = 42")
    assert permissive_chain.state == ChainState.MODIFIED

    _ = permissive_chain.value
    assert permissive_chain.state == ChainState.COMPLETED


def test_chain_conversion(permissive_chain):
    permissive_chain.execute_code("_value = 42")

    import_chain = permissive_chain.to_import_chain()
    assert import_chain.value == 42

    access_chain = permissive_chain.to_access_chain()
    assert access_chain.value == 42


# Complex execution tests
def test_complex_execution(permissive_chain):
    code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)
_value = factorial(5)
"""
    result = permissive_chain.execute_code(code)
    assert result.value == 120


def test_multiple_operations(permissive_chain):
    permissive_chain.execute_code("x = 10")
    permissive_chain.execute_code("y = 20")
    result = permissive_chain.eval_expression("x + y")
    assert result.value == 30


def test_error_output_capture(permissive_chain):
    permissive_chain.execute_code("""
import sys
print('error message', file=sys.stderr)
""")
    assert "error message" in permissive_chain.error_output
