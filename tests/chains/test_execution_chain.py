import types
import pytest
from pypaya_python_tools.chains.execution import ExecutionChain
from pypaya_python_tools.chains.base.state import ChainState
from pypaya_python_tools.execution.exceptions import ExecutionError, ExecutionSecurityError
from pypaya_python_tools.code_analysis import (
    StringPatternAnalyzer, ImportAnalyzer, SecurityAnalyzerChain
)


@pytest.fixture
def permissive_analyzer():
    """Security analyzer that allows most operations"""
    return None  # No security analyzer means everything is allowed


@pytest.fixture
def restricted_analyzer():
    """Security analyzer that restricts most operations"""
    return SecurityAnalyzerChain([
        StringPatternAnalyzer(forbidden_patterns=["eval(", "exec("]),
        ImportAnalyzer(
            blocked_modules={"os", "sys", "subprocess"},
            default_policy="allow"
        )
    ])


@pytest.fixture
def permissive_chain(permissive_analyzer):
    return ExecutionChain(security_analyzer=permissive_analyzer)


@pytest.fixture
def restricted_chain(restricted_analyzer):
    return ExecutionChain(security_analyzer=restricted_analyzer)


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
        restricted_chain.eval_expression("eval('2 + 2')")
    assert "Forbidden pattern" in str(exc_info.value)


def test_compile_denied(restricted_chain):
    with pytest.raises(ExecutionError) as exc_info:
        restricted_chain.compile_code("exec('x = 1')")
    assert "Security violations" in str(exc_info.value)


def test_subprocess_denied(restricted_chain):
    with pytest.raises(ExecutionSecurityError) as exc_info:
        restricted_chain.execute_code("import subprocess")
    assert "Unauthorized import" in str(exc_info.value)


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


def test_skip_security_check(restricted_chain):
    """Test that skip_security_check allows executing code that would normally be blocked"""
    # First part: verify code is blocked
    analyzer = SecurityAnalyzerChain([
        ImportAnalyzer(blocked_modules={"subprocess"}, default_policy="allow")
    ])
    chain1 = ExecutionChain(security_analyzer=analyzer)

    with pytest.raises(ExecutionSecurityError):
        chain1.execute_code("import subprocess")

    # Second part: create a new chain and verify skip_security_check works
    chain2 = ExecutionChain(security_analyzer=analyzer)
    result = chain2.execute_code("import subprocess", skip_security_check=True)
    assert result.last_result.error is None


def test_analyze_code(restricted_chain):
    violations = restricted_chain.analyze_code("import os; eval('os.system(\"ls\")')")
    assert len(violations) >= 2  # Should catch both import and eval
    assert any("import" in v.lower() for v in violations)
    assert any("eval" in v.lower() for v in violations)

    # Clean code should have no violations
    violations = restricted_chain.analyze_code("x = 42; print(x)")
    assert len(violations) == 0
