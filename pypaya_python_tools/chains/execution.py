from typing import Any, Optional, Dict, List, Union
from pypaya_python_tools.chains.base.chain import ObjectChain
from pypaya_python_tools.chains.base.context import ChainContext
from pypaya_python_tools.chains.base.operations import ChainOperationType
from pypaya_python_tools.chains.base.state import ChainState
from pypaya_python_tools.code_analysis import (
    CodeSecurityAnalyzer, SecurityAnalyzerChain
)
from pypaya_python_tools.execution.repl import PythonREPL, ExecutionResult
from pypaya_python_tools.execution.exceptions import ExecutionError


class ExecutionChain(ObjectChain[Any]):
    """
    Chain for code execution operations.

    Provides a fluent interface for executing Python code with:
    - Code execution and expression evaluation
    - Output capture and error handling
    - State management
    - Security controls
    """

    def __init__(
            self,
            value: Optional[Any] = None,
            context: Optional[ChainContext] = None,
            security_analyzer: Optional[Union[CodeSecurityAnalyzer, List[CodeSecurityAnalyzer]]] = None
    ):
        super().__init__(value=value, context=context)

        # If security_analyzer is a list of analyzers, create a chain
        if isinstance(security_analyzer, list):
            security_analyzer = SecurityAnalyzerChain(security_analyzer)

        self._security_analyzer = security_analyzer
        self._repl = PythonREPL(security_analyzer=self._security_analyzer)

        # Initialize REPL with current value if exists
        if self._value is not None:
            self._repl.locals["_value"] = self._value

        # Store last execution result
        self._last_result: Optional[ExecutionResult] = None

    @property
    def output(self) -> Optional[str]:
        """Get the stdout from last execution."""
        return self._last_result.stdout if self._last_result else None

    @property
    def error_output(self) -> Optional[str]:
        """Get the stderr from last execution."""
        return self._last_result.stderr if self._last_result else None

    @property
    def last_result(self) -> Optional[ExecutionResult]:
        """Get complete result of last execution."""
        return self._last_result

    def execute_code(self, code: str, skip_security_check: bool = False) -> "ExecutionChain":
        """
        Execute arbitrary Python code.

        The code can modify the chain's value through '_value' variable.
        Captures both stdout and stderr.

        Args:
            code: Python code to execute
            skip_security_check: Whether to skip security analysis
        """
        self._ensure_state([ChainState.INITIAL, ChainState.LOADED, ChainState.MODIFIED])

        try:
            # Execute code
            self._last_result = self._repl.execute(code, skip_security_check=skip_security_check)

            # Update value if modified in execution
            if "_value" in self._repl.locals:
                self._value = self._repl.locals["_value"]

            self._state = ChainState.MODIFIED
            self._record_operation(
                ChainOperationType.EXECUTE,
                "execute_code",
                True,
                None,
                code=code,
                result=self._last_result
            )

            if self._last_result.error:
                raise ExecutionError(self._last_result.error)

        except Exception as e:
            self._state = ChainState.FAILED
            self._last_error = e
            self._record_operation(
                ChainOperationType.EXECUTE,
                "execute_code",
                False,
                e,
                code=code
            )
            raise

        return self

    def eval_expression(self, expr: str, skip_security_check: bool = False) -> "ExecutionChain":
        """
        Evaluate a Python expression and store its result.

        The result becomes the new chain value.

        Args:
            expr: Python expression to evaluate
            skip_security_check: Whether to skip security analysis
        """
        self._ensure_state([ChainState.INITIAL, ChainState.LOADED, ChainState.MODIFIED])

        try:
            # Evaluate expression
            self._last_result = self._repl.eval(expr, skip_security_check=skip_security_check)

            # Update chain value with evaluation result
            self._value = self._last_result.result

            self._state = ChainState.MODIFIED
            self._record_operation(
                ChainOperationType.EXECUTE,
                "eval_expression",
                True,
                None,
                expression=expr,
                result=self._last_result
            )

            if self._last_result.error:
                raise ExecutionError(self._last_result.error)

        except Exception as e:
            self._state = ChainState.FAILED
            self._last_error = e
            self._record_operation(
                ChainOperationType.EXECUTE,
                "eval_expression",
                False,
                e,
                expression=expr
            )
            raise

        return self

    def compile_code(self, code: str, mode: str = "exec") -> "ExecutionChain":
        """
        Compile code without executing it.

        The compiled code object becomes the new chain value.
        """
        self._ensure_state([ChainState.INITIAL, ChainState.LOADED, ChainState.MODIFIED])

        try:
            # Analyze code security first
            if self._security_analyzer:
                violations = self._security_analyzer.analyze(code)
                if violations:
                    violation_msgs = [str(v) for v in violations]
                    raise ExecutionError(f"Security violations in code:\n" + "\n".join(violation_msgs))

            # Compile code
            compiled = self._repl.compile(code, mode)
            self._value = compiled

            self._state = ChainState.MODIFIED
            self._record_operation(
                ChainOperationType.EXECUTE,
                "compile_code",
                True,
                None,
                code=code,
                mode=mode
            )

        except Exception as e:
            self._state = ChainState.FAILED
            self._last_error = e
            self._record_operation(
                ChainOperationType.EXECUTE,
                "compile_code",
                False,
                e,
                code=code,
                mode=mode
            )
            raise

        return self

    def with_globals(self, globals_dict: Dict[str, Any]) -> "ExecutionChain":
        """Set global variables for execution context"""
        self._repl.globals.update(globals_dict)
        return self

    def with_locals(self, locals_dict: Dict[str, Any]) -> "ExecutionChain":
        """Set local variables for execution context"""
        self._repl.locals.update(locals_dict)
        return self

    def analyze_code(self, code: str) -> List[str]:
        """
        Analyze code for security violations without executing it

        Args:
            code: Python code to analyze

        Returns:
            List of security violation messages (empty if code is safe)
        """
        if self._security_analyzer:
            violations = self._security_analyzer.analyze(code)
            return [str(v) for v in violations]
        return []

    def to_import_chain(self) -> "ImportChain":
        from pypaya_python_tools.chains.importing import ImportChain
        return ImportChain(value=self._value, context=self._context.clone())

    def to_access_chain(self) -> "AccessChain":
        from pypaya_python_tools.chains.object_operation import OperationChain
        return OperationChain(value=self._value, context=self._context.clone())

    def to_execution_chain(self) -> "ExecutionChain":
        return self
