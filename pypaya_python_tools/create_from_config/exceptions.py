

class ConfigError(Exception):
    """Base exception for configuration-related errors."""
    pass


class ImportingError(ConfigError):
    """Raised when object import fails."""
    pass


class ValidationError(ConfigError):
    """Raised when configuration validation fails."""
    pass


class InstantiationError(ConfigError):
    """Raised when object instantiation fails."""
    pass
