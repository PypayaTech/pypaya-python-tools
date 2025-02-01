

class ObjectAccessError(Exception):
    """Base exception for object access errors."""
    pass


class AccessError(ObjectAccessError):
    """Base class for access operation errors."""
    pass


class InstantiationError(AccessError):
    """Error during object instantiation."""
    pass


class CallError(AccessError):
    """Error during object calling."""
    pass


class BuilderError(ObjectAccessError):
    """Base class for builder errors."""
    pass


class InvalidStateError(BuilderError):
    """Raised when builder is used in invalid state."""
    pass


class ObjectAccessSecurityError(ObjectAccessError):
    """Raised when security constraints are violated during object access."""
    pass
