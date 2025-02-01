from abc import ABC
from typing import TypeVar, Generic, Optional
from pypaya_python_tools.chains.base.context import ChainContext
from pypaya_python_tools.chains.base.operations import ChainOperationType
from pypaya_python_tools.chains.base.state import ChainState
from pypaya_python_tools.chains.exceptions import ChainStateError


T = TypeVar('T')


class ObjectChain(Generic[T], ABC):
    """Base class for all chain operations"""

    def __init__(
        self,
        value: Optional[T] = None,
        context: Optional[ChainContext] = None
    ):
        self._value = value
        self._state = ChainState.INITIAL if value is None else ChainState.LOADED
        self._context = context or ChainContext()
        self._last_error: Optional[Exception] = None

    @property
    def value(self) -> T:
        """Get the current value in the chain"""
        if self._state == ChainState.FAILED:
            raise ChainStateError("Cannot get value from failed chain")
        self._state = ChainState.COMPLETED
        return self._value

    @property
    def state(self) -> ChainState:
        """Get current chain state"""
        return self._state

    @property
    def context(self) -> ChainContext:
        """Get chain context"""
        return self._context

    def _ensure_state(self, expected: set[ChainState]) -> None:
        """Ensure chain is in one of the expected states"""
        if self._state not in expected:
            raise ChainStateError(
                f"Invalid chain state. Expected one of {[e.name for e in expected]}, "
                f"got {self._state.name}"
            )

    def _record_operation(
        self,
        operation_type: ChainOperationType,
        method_name: str = "",
        success: bool = True,
        error: Optional[Exception] = None,
        *args,
        **kwargs
    ) -> None:
        """Record an operation in the context"""
        record = self._context.record_operation(
            operation_type,
            method_name,
            *args,
            **kwargs
        )
        record.result.success = success
        record.result.error = error
        record.result.value = self._value if success else None

    def __enter__(self) -> "ObjectChain[T]":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_val:
            self._state = ChainState.FAILED
            self._last_error = exc_val
