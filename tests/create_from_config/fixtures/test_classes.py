from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SimpleClass:
    value: str


@dataclass
class ComplexClass:
    nested: SimpleClass
    optional: Optional[str] = None


class AbstractClass(ABC):
    @abstractmethod
    def abstract_method(self):
        pass


class NonDataClass:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


class CallableClass:
    def __init__(self, factor=1):
        self.factor = factor

    def __call__(self, value):
        return value * self.factor


class Calculator:
    def add(self, a, b):
        return a + b
