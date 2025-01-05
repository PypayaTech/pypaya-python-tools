from abc import ABC, abstractmethod
from typing import Any, Dict, TypeVar, Generic
from dataclasses import dataclass
from pypaya_python_tools.importing.security import SecurityContext
from pypaya_python_tools.importing.definitions import ImportSource


T = TypeVar('T')


@dataclass
class ResolveResult(Generic[T]):
    """Result of a successful resolution."""
    value: T
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ImportResolver(ABC):
    """Base class for all import resolvers."""

    def __init__(self, security_context: SecurityContext):
        self.security = security_context

    @abstractmethod
    def can_handle(self, source: ImportSource) -> bool:
        """Check if this resolver can handle the source."""
        pass

    @abstractmethod
    def resolve(self, source: ImportSource) -> ResolveResult:
        """
        Resolve and return the requested object.

        Args:
            source: Import source specification

        Returns:
            ResolveResult containing the resolved object and metadata

        Raises:
            ResolverError: If resolution fails
        """
        pass

    def _validate_source(self, source: ImportSource) -> None:
        """Validate source before resolution."""
        pass
