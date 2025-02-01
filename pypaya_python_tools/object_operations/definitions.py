from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Optional, Generic, TypeVar, Union, Mapping


# Type variables for generic operations
T = TypeVar('T')  # For operation result value
M = TypeVar('M')  # For metadata


# Custom type for metadata to ensure type safety
MetadataType = Mapping[str, Any]


class OperationType(Enum):
    """Types of object operations.

    Each type represents a distinct operation category:
    - DIRECT: Direct object access without modification
    - GET_ATTRIBUTE: Get object attribute by name
    - SET_ATTRIBUTE: Set object attribute value
    - DEL_ATTRIBUTE: Delete object attribute
    - CALL: Call object (functions, methods, callables)
    - INSTANTIATE: Create new class instance
    - GET_ITEM: Get container item by key/index
    - SET_ITEM: Set container item value
    - DEL_ITEM: Delete container item
    - ITERATE: Get iterator for object
    """
    DIRECT = auto()  # Direct object access
    GET_ATTRIBUTE = auto()  # Get attribute
    SET_ATTRIBUTE = auto()  # Set attribute
    DEL_ATTRIBUTE = auto()  # Delete attribute
    CALL = auto()  # Function/method calling
    INSTANTIATE = auto()  # Class instantiation
    GET_ITEM = auto()  # Container item access
    SET_ITEM = auto()  # Container item setting
    DEL_ITEM = auto()  # Container item deletion
    ITERATE = auto()  # Iterator access


@dataclass
class Operation:
    """Operation specification.

    Attributes:
        type: Type of operation to perform
        args: Positional arguments for the operation
        kwargs: Keyword arguments for the operation
        metadata: Optional operation metadata
    """
    type: OperationType
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    metadata: MetadataType = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure immutable args and kwargs."""
        # Convert args to tuple if it isn't already
        if not isinstance(self.args, tuple):
            self.args = tuple(self.args)

        # Create new dict for kwargs if needed
        if not isinstance(self.kwargs, dict):
            self.kwargs = dict(self.kwargs)

        # Create new dict for metadata if needed
        if not isinstance(self.metadata, dict):
            self.metadata = dict(self.metadata)


@dataclass
class OperationResult(Generic[T]):
    """Result of an operation.

    Attributes:
        success: Whether the operation succeeded
        value: Result value (type depends on operation)
        error: Optional error if operation failed
        metadata: Optional operation result metadata
    """
    success: bool
    value: Optional[T] = None
    error: Optional[Exception] = None
    metadata: MetadataType = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate result state."""
        # Ensure consistent state
        if self.success and self.error is not None:
            raise ValueError("Success result cannot have an error")
        if not self.success and self.error is None:
            raise ValueError("Failed result must have an error")

        # Create new dict for metadata if needed
        if not isinstance(self.metadata, dict):
            self.metadata = dict(self.metadata)
