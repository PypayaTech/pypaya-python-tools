

class ChainError(Exception):
    """Base exception for chain operations"""
    pass


class ChainStateError(ChainError):
    """Invalid chain state"""
    pass
