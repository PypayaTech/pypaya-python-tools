from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, Any, Union
from pathlib import Path


class ObjectType(Enum):
    """Types of objects that can be created/accessed."""
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    CLASS_METHOD = "classmethod"
    STATIC_METHOD = "staticmethod"
    PROPERTY = "property"
    CALLABLE_CLASS = "callable_class"
    GENERATOR = "generator"
    COROUTINE = "coroutine"
    BUILTIN = "builtin"
    MODULE = "module"
    PARTIAL = "partial"


class AccessType(Enum):
    """Ways to access/use objects."""
    DIRECT = auto()      # Direct object access
    INSTANTIATE = auto() # Class instantiation
    CALL = auto()        # Function/method calling
    GET = auto()         # Attribute/property access
    SET = auto()         # Attribute setting
    MODIFY = auto()      # Object modification


@dataclass
class ObjectConfig:
    """Configuration for object access and manipulation."""
    # Source specification (where to get the object from)
    type: ObjectType
    module: Optional[str] = None  # Module path (e.g., "mypackage.module")
    file: Optional[str] = None  # File path (e.g., "/path/to/file.py")
    name: Optional[str] = None  # Object name within module/file

    # Creation/access specification
    args: tuple = ()  # Positional arguments
    kwargs: Dict[str, Any] = field(default_factory=dict)  # Keyword arguments
    instance_config: Optional[Dict[str, Any]] = None  # For methods: how to create instance

    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}


@dataclass
class ObjectAccess:
    """Specification of how to access/use an object."""
    type: AccessType
    args: tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}


@dataclass
class AccessResult:
    """Result of an access operation."""
    value: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
