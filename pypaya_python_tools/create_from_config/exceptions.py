

class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass


class ValidationError(ConfigError):
    """Configuration validation failed."""
    pass


class InstantiationError(ConfigError):
    """Object instantiation failed."""
    pass


class CallableCreationError(ConfigError):
    """Callable creation failed."""
    pass
