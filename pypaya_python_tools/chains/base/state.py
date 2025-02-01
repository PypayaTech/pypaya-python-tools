from enum import Enum, auto


class ChainState(Enum):
    """States of chain operations"""
    INITIAL = auto()      # Chain just created
    LOADED = auto()       # Value loaded/imported
    MODIFIED = auto()     # Value modified
    COMPLETED = auto()    # Chain operations completed
    FAILED = auto()       # Operation failed
