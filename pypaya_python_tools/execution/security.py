from dataclasses import dataclass, field
from typing import Set, Optional, Pattern, Union
from pypaya_python_tools.execution.exceptions import ExecutionSecurityError


@dataclass
class ExecutionSecurity:
    """Security controls for code execution"""

    # Basic controls
    enabled: bool = True

    # Resource limits
    max_time: Optional[int] = 30  # seconds
    max_memory: Optional[int] = 100_000_000  # bytes
    max_cpu_percent: Optional[float] = 90.0

    # Execution controls
    allow_eval: bool = False
    allow_exec: bool = False
    allow_compile: bool = False
    allow_subprocess: bool = False

    # Module access
    allowed_modules: Set[str] = field(default_factory=set)
    blocked_modules: Set[str] = field(default_factory=set)

    # Builtin access
    allowed_builtins: Set[str] = field(default_factory=set)
    blocked_builtins: Set[str] = field(default_factory=set)

    def validate_execution(self, code: str) -> None:
        """Validate code execution"""
        if not self.enabled:
            return

        if "eval(" in code and not self.allow_eval:
            raise ExecutionSecurityError("eval() is not allowed")
        if "exec(" in code and not self.allow_exec:
            raise ExecutionSecurityError("exec() is not allowed")
        if "subprocess" in code and not self.allow_subprocess:
            raise ExecutionSecurityError("subprocess usage is not allowed")
        # More validation could be added (e.g., AST analysis)
