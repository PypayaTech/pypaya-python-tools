

class CodePresenterError(Exception):
    """Base exception for CodePresenter errors."""
    pass


class InvalidPathError(CodePresenterError):
    """Raised when a path is invalid or doesn't exist."""
    pass


class FileAccessError(CodePresenterError):
    """Raised when there's an error accessing a file."""
    pass
