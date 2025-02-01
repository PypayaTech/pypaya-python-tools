

class ExecutionError(Exception):
    """Base exception for execution-related errors."""
    pass


class ExecutionSecurityError(ExecutionError):
    """Security-related execution errors."""
    pass
