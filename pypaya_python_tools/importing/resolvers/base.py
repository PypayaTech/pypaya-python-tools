from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, TypeVar, Generic
from pypaya_python_tools.importing.security import ImportSecurity
from pypaya_python_tools.importing.source import ImportSource


T = TypeVar('T')


@dataclass
class ResolveResult(Generic[T]):
    """Result of import resolution."""
    value: T
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ImportResolver(ABC):
    """Base class for import resolvers."""

    def __init__(self, security: ImportSecurity):
        self.security = security

    @abstractmethod
    def can_handle(self, source: ImportSource) -> bool:
        """Check if this resolver can handle the source."""
        pass

    def resolve(self, source: ImportSource) -> ResolveResult:
        """Template method for resolution with security."""
        try:
            self.security.enter_level()
            return self._do_resolve(source)
        finally:
            self.security.exit_level()

    @abstractmethod
    def _do_resolve(self, source: ImportSource) -> ResolveResult:
        """Actual resolution implementation."""
        pass
