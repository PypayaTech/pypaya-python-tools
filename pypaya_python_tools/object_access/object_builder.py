from typing import Any, Optional, Dict, TypeVar, Generic, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum, auto
from pypaya_python_tools.importing.definitions import SourceType, ImportSource
from pypaya_python_tools.object_access.definitions import AccessType, ObjectAccess
from pypaya_python_tools.importing.import_manager import ImportManager
from pypaya_python_tools.object_access.access_manager import AccessManager
from pypaya_python_tools.object_access.exceptions import InvalidStateError
#from pypaya_python_tools.importing.security import SecurityContext, DEFAULT_SECURITY


T = TypeVar('T')


class BuilderState(Enum):
    """States of the builder process."""
    INITIAL = auto()        # No source specified yet
    SOURCE_SET = auto()     # Source specified but not imported
    OBJECT_LOADED = auto()  # Object imported
    MODIFIED = auto()       # Object modified (instantiated/configured)
    COMPLETED = auto()      # Build process completed


@dataclass
class BuilderContext(Generic[T]):
    """Context holding the builder's state and data."""
    state: BuilderState = BuilderState.INITIAL
    source: Optional[ImportSource] = None
    imported_object: Optional[Any] = None
    current_object: Optional[T] = None
    modifications: list[ObjectAccess] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ObjectBuilder(Generic[T]):
    """
    Fluent interface for importing and manipulating objects.

    Example:
        result = (ObjectBuilder()
                 .from_module("myapp.handlers")
                 .get_class("DataHandler")
                 .instantiate(timeout=30)
                 .configure({"retries": 3})
                 .call_method("initialize")
                 .build())
    """

    def __init__(self):
        self.import_manager = ImportManager()
        self.access_manager = AccessManager()
        self.context = BuilderContext[T]()

    def from_module(self, module_path: str) -> 'ObjectBuilder[T]':
        """Specify module source."""
        self._ensure_state(BuilderState.INITIAL)
        self.context.source = ImportSource(
            type=SourceType.MODULE,
            location=module_path
        )
        self.context.state = BuilderState.SOURCE_SET
        return self

    def from_file(self, file_path: Union[str, Path]) -> 'ObjectBuilder[T]':
        """Specify file source."""
        self._ensure_state(BuilderState.INITIAL)
        self.context.source = ImportSource(
            type=SourceType.FILE,
            location=file_path
        )
        self.context.state = BuilderState.SOURCE_SET
        return self

    def from_builtin(self) -> 'ObjectBuilder[T]':
        """Specify builtin source."""
        self._ensure_state(BuilderState.INITIAL)
        self.context.source = ImportSource(
            type=SourceType.BUILTIN
        )
        self.context.state = BuilderState.SOURCE_SET
        return self

    def get_class(self, name: str) -> 'ObjectBuilder[T]':
        """Get class from source."""
        self._ensure_state(BuilderState.SOURCE_SET)
        self.context.source.name = name
        self.context.imported_object = self.import_manager.import_object(self.context.source)
        self.context.current_object = self.context.imported_object
        self.context.state = BuilderState.OBJECT_LOADED
        return self

    def instantiate(self, *args, **kwargs) -> 'ObjectBuilder[T]':
        """Instantiate the loaded class."""
        self._ensure_state(BuilderState.OBJECT_LOADED)
        access = ObjectAccess(
            type=AccessType.INSTANTIATE,
            args=args,
            kwargs=kwargs
        )
        self.context.modifications.append(access)
        self.context.current_object = self.access_manager.access_object(
            self.context.current_object,
            access
        )
        self.context.state = BuilderState.MODIFIED
        return self

    def get_attribute(self, name: str) -> 'ObjectBuilder[T]':
        """Get object attribute by name."""
        self._ensure_state([BuilderState.OBJECT_LOADED, BuilderState.MODIFIED])
        access = ObjectAccess(
            type=AccessType.GET,
            args=(name,)
        )
        self.context.modifications.append(access)
        self.context.current_object = self.access_manager.access_object(
            self.context.current_object,
            access
        )
        self.context.state = BuilderState.MODIFIED
        return self

    def set_attribute(self, name: str, value: Any) -> 'ObjectBuilder[T]':
        """Set object attribute value."""
        self._ensure_state([BuilderState.OBJECT_LOADED, BuilderState.MODIFIED])
        access = ObjectAccess(
            type=AccessType.SET,
            args=(name, value)
        )
        self.context.modifications.append(access)
        self.access_manager.access_object(
            self.context.current_object,
            access
        )
        return self

    def configure(self, config: Dict[str, Any]) -> 'ObjectBuilder[T]':
        """Configure multiple object attributes."""
        self._ensure_state([BuilderState.OBJECT_LOADED, BuilderState.MODIFIED])
        for key, value in config.items():
            self.set_attribute(key, value)
        return self

    def call_method(self, method_name: str, *args, **kwargs) -> 'ObjectBuilder[T]':
        """Call method on the object."""
        self._ensure_state([BuilderState.OBJECT_LOADED, BuilderState.MODIFIED])

        # First get the method
        method = self.access_manager.access_object(
            self.context.current_object,
            ObjectAccess(type=AccessType.GET, args=(method_name,))
        )

        # Then call it
        result = self.access_manager.access_object(
            method,
            ObjectAccess(type=AccessType.CALL, args=args, kwargs=kwargs)
        )

        self.context.current_object = result
        self.context.state = BuilderState.MODIFIED
        return self

    def build(self) -> T:
        """Complete the build process and return the result."""
        if self.context.state == BuilderState.INITIAL:
            raise InvalidStateError("No source specified")

        self.context.state = BuilderState.COMPLETED
        return self.context.current_object

    def _ensure_state(self, expected: Union[BuilderState, list[BuilderState]]) -> None:
        """Ensure builder is in expected state."""
        if isinstance(expected, BuilderState):
            expected = [expected]
        if self.context.state not in expected:
            raise InvalidStateError(
                f"Invalid builder state. Expected one of {[e.name for e in expected]}, "
                f"got {self.context.state.name}"
            )
