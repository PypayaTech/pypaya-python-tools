import functools
import logging
import sys
from dataclasses import dataclass
from io import StringIO
from typing import Dict, Optional, Tuple, Any
from pypaya_python_tools.execution.exceptions import ExecutionError, ExecutionSecurityError
from pypaya_python_tools.execution.security import ExecutionSecurity


logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=None)
def warn_once() -> None:
    """Warn once about the dangers of PythonREPL."""
    logger.warning("Python REPL can execute arbitrary code. Use with caution.")


@dataclass
class ExecutionResult:
    """Encapsulates the result of code execution."""
    stdout: str = ''
    stderr: str = ''
    result: Any = None
    error: Optional[str] = None

    def __str__(self) -> str:
        if self.error:
            return self.error
        return self.stdout


class PythonREPL:
    """Simulates a standalone Python REPL."""

    def __init__(self, security: Optional[ExecutionSecurity] = None):
        self.globals: Dict[str, Any] = {}
        self.locals: Dict[str, Any] = {}
        self._security = security or ExecutionSecurity()

    def _execute_code(self, code: str, mode: str) -> Dict:
        """Execute code and return result dictionary."""
        stdout = StringIO()
        stderr = StringIO()

        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = stdout, stderr

        try:
            if mode == "eval":
                result = eval(code, self.globals, self.locals)
                return {
                    "result": result,
                    "stdout": stdout.getvalue(),
                    "stderr": stderr.getvalue()
                }
            else:
                exec(code, self.globals, self.locals)
                return {
                    "result": None,
                    "stdout": stdout.getvalue(),
                    "stderr": stderr.getvalue()
                }
        except Exception as e:
            return {
                "error": repr(e),
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue()
            }
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
            stdout.close()
            stderr.close()

    def _dict_to_execution_result(self, result_dict: Dict) -> ExecutionResult:
        """Convert a result dictionary to an ExecutionResult object."""
        if "error" in result_dict:
            return ExecutionResult(
                stdout=result_dict["stdout"],
                stderr=result_dict["stderr"],
                error=result_dict["error"]
            )
        return ExecutionResult(
            stdout=result_dict["stdout"],
            stderr=result_dict["stderr"],
            result=result_dict.get("result")
        )

    def execute(self, code: str, mode: str = "exec") -> ExecutionResult:
        """Execute code and return comprehensive result."""
        warn_once()
        self._security.validate_execution(code)
        result_dict = self._execute_code(code, mode)
        return self._dict_to_execution_result(result_dict)

    def eval(self, expr: str) -> ExecutionResult:
        """Evaluate an expression and return its value."""
        if not self._security.allow_eval:
            raise ExecutionSecurityError("eval() is not allowed")
        return self.execute(expr, mode="eval")

    def compile(self, code: str, mode: str = "exec") -> Any:
        """Compile code without executing it."""
        if not self._security.allow_compile:
            raise ExecutionSecurityError("compile() is not allowed")
        return compile(code, "<string>", mode)


def main():
    repl = PythonREPL(security=ExecutionSecurity(allow_eval=True))

    print("\n=== 1. Basic Expression Evaluation ===")
    result = repl.eval("2 + 2")
    print(f"Simple math result: {result.result}")  # Should print 4

    print("\n=== 2. Variable Assignment and State ===")
    result = repl.execute("x = 42")
    print(f"Assignment output: {result}")
    print(f"Locals after assignment: {repl.locals}")

    result = repl.eval("x + 8")
    print(f"Using variable result: {result.result}")  # Should print 50

    print("\n=== 3. Print Statement Capture ===")
    result = repl.execute('print("Hello, World!")')
    print(f"Captured output: {result.stdout}")  # Should print Hello, World!

    print("\n=== 4. Function Definition and Usage ===")
    result = repl.execute("""
def greet(name):
    return f"Hello, {name}!"
""")
    print(f"Function definition output: {result}")

    result = repl.eval('greet("Python")')
    print(f"Function call result: {result.result}")  # Should print Hello, Python!

    print("\n=== 5. Error Handling ===")
    result = repl.execute("1/0")
    print(f"Division by zero error: {result.error}")

    result = repl.execute("undefined_variable")
    print(f"Undefined variable error: {result.error}")

    print("\n=== 6. Multi-line Code ===")
    code = """
total = 0
for i in range(5):
    total += i
print(f"Total: {total}")
"""
    result = repl.execute(code)
    print(f"Multi-line code output: {result.stdout}")

    print("\n=== 7. Complex Data Structures ===")
    result = repl.execute("data = {'name': 'Alice', 'scores': [1, 2, 3]}")
    print(f"Dict creation output: {result}")

    result = repl.eval("data['scores']")
    print(f"Accessing dict result: {result.result}")


if __name__ == "__main__":
    main()
