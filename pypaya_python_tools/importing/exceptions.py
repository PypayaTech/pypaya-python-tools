

class ImportingError(Exception):
    """Base exception for import-related errors."""
    pass


class ImportingSecurityError(ImportingError):
    """Security-related import errors."""
    pass


class ResolverError(ImportingError):
    """Resolver-specific errors."""
    pass
