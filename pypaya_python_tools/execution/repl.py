import functools
import logging
import sys
from dataclasses import dataclass
from io import StringIO
from typing import Dict, Optional, Any, List
from pypaya_python_tools.execution.exceptions import ExecutionSecurityError
from pypaya_python_tools.code_analysis.base import CodeSecurityAnalyzer


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
    security_violations: List[str] = None

    def __post_init__(self):
        if self.security_violations is None:
            self.security_violations = []

    def __str__(self) -> str:
        if self.error:
            return self.error
        return self.stdout


class PythonREPL:
    """Simulates a standalone Python REPL with security analysis."""

    def __init__(self, security_analyzer: Optional[CodeSecurityAnalyzer] = None):
        """
        Initialize REPL with optional security analyzer

        Args:
            security_analyzer: CodeSecurityAnalyzer to use for code validation
        """
        self.globals: Dict[str, Any] = {}
        self.locals: Dict[str, Any] = {}
        self.security_analyzer = security_analyzer

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

    def _dict_to_execution_result(self, result_dict: Dict, security_violations: List[str] = None) -> ExecutionResult:
        """Convert a result dictionary to an ExecutionResult object."""
        if "error" in result_dict:
            return ExecutionResult(
                stdout=result_dict["stdout"],
                stderr=result_dict["stderr"],
                error=result_dict["error"],
                security_violations=security_violations or []
            )
        return ExecutionResult(
            stdout=result_dict["stdout"],
            stderr=result_dict["stderr"],
            result=result_dict.get("result"),
            security_violations=security_violations or []
        )

    def execute(self, code: str, mode: str = "exec", skip_security_check: bool = False) -> ExecutionResult:
        """
        Execute code and return comprehensive result.

        Args:
            code: Python code to execute
            mode: 'exec' or 'eval'
            skip_security_check: Whether to bypass security analysis

        Returns:
            ExecutionResult containing execution output and any security violations

        Raises:
            ExecutionSecurityError: If code fails security analysis
        """
        warn_once()

        # Perform security analysis if an analyzer is configured
        security_violations = []
        if self.security_analyzer and not skip_security_check:
            violations = self.security_analyzer.analyze(code)
            if violations:
                security_violations = [str(v) for v in violations]
                violation_report = "\n".join(security_violations)
                raise ExecutionSecurityError(f"Security violations detected:\n{violation_report}")

        # Execute the code
        result_dict = self._execute_code(code, mode)
        return self._dict_to_execution_result(result_dict, security_violations)

    def eval(self, expr: str, skip_security_check: bool = False) -> ExecutionResult:
        """
        Evaluate an expression and return its value.

        Args:
            expr: Python expression to evaluate
            skip_security_check: Whether to bypass security analysis

        Returns:
            ExecutionResult with the expression's value

        Raises:
            ExecutionSecurityError: If code fails security analysis
        """
        return self.execute(expr, mode="eval", skip_security_check=skip_security_check)

    def compile(self, code: str, mode: str = "exec") -> Any:
        """
        Compile code without executing it.

        Args:
            code: Python code to compile
            mode: Compilation mode ('exec', 'eval', or 'single')

        Returns:
            Compiled code object
        """
        return compile(code, "<string>", mode)

    def analyze(self, code: str) -> List[str]:
        """
        Analyze code for security violations without executing it.

        Args:
            code: Python code to analyze

        Returns:
            List of security violation messages (empty if code is safe)
        """
        if not self.security_analyzer:
            return []

        violations = self.security_analyzer.analyze(code)
        return [str(v) for v in violations]


def main():
    from pypaya_python_tools.code_analysis import (
        StringPatternAnalyzer, ImportAnalyzer, SecurityAnalyzerChain
    )

    # Create a security analyzer chain
    analyzer = SecurityAnalyzerChain([
        StringPatternAnalyzer(forbidden_patterns=["eval(", "exec(", "import os"]),
        ImportAnalyzer(blocked_modules={"os", "subprocess", "sys"})
    ])

    # Initialize REPL with security analyzer
    repl = PythonREPL(security_analyzer=analyzer)

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

    print("\n=== 8. Security Analysis ===")
    try:
        repl.execute("import os")
        print("This should not be printed")
    except ExecutionSecurityError as e:
        print(f"Security error (expected): {e}")

    try:
        repl.execute("eval('os.system(\"ls\")')")
        print("This should not be printed")
    except ExecutionSecurityError as e:
        print(f"Security error (expected): {e}")

    # Analyze without executing
    violations = repl.analyze("import subprocess; subprocess.run(['rm', '-rf', '/'])")
    print(f"Security violations: {len(violations)}")
    for v in violations:
        print(f"- {v}")


if __name__ == "__main__":
    main()
