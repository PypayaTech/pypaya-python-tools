from abc import ABC, abstractmethod
from typing import Any, Dict, TypeVar, Generic
from dataclasses import dataclass
from pypaya_python_tools.object_access.security import ObjectAccessSecurityContext
from pypaya_python_tools.object_access.definitions import ObjectAccess


T = TypeVar('T')


@dataclass
class AccessResult(Generic[T]):
    """Result of an access operation."""
    value: T
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AccessHandler(ABC):
    """Base class for all access handlers."""

    def __init__(self, security_context: ObjectAccessSecurityContext):
        self.security = security_context

    @abstractmethod
    def can_handle(self, obj: Any, access: ObjectAccess) -> bool:
        """Check if this handler can handle the access type for the object."""
        pass

    @abstractmethod
    def handle(self, obj: Any, access: ObjectAccess) -> AccessResult:
        """
        Handle the access operation.

        Args:
            obj: The object to access
            access: Access specification

        Returns:
            AccessResult containing the result and metadata

        Raises:
            AccessError: If access operation fails
        """
        pass

    def _validate_access(self, obj: Any, access: ObjectAccess) -> None:
        """Validate access before handling."""
        pass
