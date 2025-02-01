from enum import Enum, auto


class ChainOperationType(Enum):
    """Types of operations that can be performed in chains"""
    IMPORT = auto()    # Import operations
    ACCESS = auto()    # Object access operations
    EXECUTE = auto()   # Code execution operations
