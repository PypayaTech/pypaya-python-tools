

class ImportingError(Exception):
    """Base exception for import-related errors."""
    pass


class ResolverError(ImportingError):
    """Raised when import resolver encounters an error."""
    pass
