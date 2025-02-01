from enum import Enum, auto


class StructureFormat(Enum):
    PLAIN = auto()
    TREE = auto()
    MARKDOWN = auto()


class ContentFormat(Enum):
    MARKDOWN = auto()
    PLAIN = auto()
