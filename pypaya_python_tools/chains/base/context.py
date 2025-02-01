from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Dict
from pypaya_python_tools.chains.base.operations import ChainOperationType


@dataclass
class OperationResult:
    """Result of a chain operation"""
    success: bool
    value: Any = None
    error: Exception = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OperationRecord:
    """Record of a chain operation."""
    operation_type: ChainOperationType
    method_name: str
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    result: OperationResult = field(default_factory=lambda: OperationResult(success=True))
    timestamp: datetime = field(default_factory=datetime.now)


class ChainContext:
    """Context for chain operations"""

    def __init__(self):
        self.operation_history: List[ChainOperationType] = []
        self.modifications: List[OperationRecord] = []
        self.metadata: Dict[str, Any] = {}

    def record_operation(
            self,
            operation_type: ChainOperationType,
            method_name: str,
            *args,
            **kwargs
    ) -> OperationRecord:
        """Record an operation."""
        record = OperationRecord(
            operation_type=operation_type,
            method_name=method_name,
            args=args,
            kwargs=kwargs
        )
        self.modifications.append(record)
        self.operation_history.append(operation_type)
        return record

    def set_metadata(self, key: str, value: Any) -> None:
        """Set context metadata."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get context metadata."""
        return self.metadata.get(key, default)

    def clone(self) -> "ChainContext":
        """Create a new context with copied data structures."""
        new_context = ChainContext()
        new_context.operation_history = self.operation_history.copy()
        new_context.modifications = [
            OperationRecord(
                operation_type=record.operation_type,
                method_name=record.method_name,
                args=record.args,
                kwargs=record.kwargs,
                result=OperationResult(
                    success=record.result.success,
                    value=record.result.value,
                    error=record.result.error,
                    timestamp=record.result.timestamp
                ),
                timestamp=record.timestamp
            )
            for record in self.modifications
        ]
        new_context.metadata = self.metadata.copy()
        return new_context
