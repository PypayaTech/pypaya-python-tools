from dataclasses import dataclass
from typing import Optional


@dataclass
class SimpleClass:
    value: str


@dataclass
class ComplexClass:
    nested: SimpleClass
    optional: Optional[str] = None


class AbstractClass:
    @property
    def abstract_property(self):
        raise NotImplementedError


class NonDataClass:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
