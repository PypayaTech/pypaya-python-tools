import pytest
from dataclasses import dataclass
from typing import List, Dict, Any


# Test classes for different scenarios
@dataclass
class SimpleDataClass:
    name: str
    value: int


class TestClass:
    def __init__(self, value: Any = None):
        self._protected = "protected"
        self.__private = "private"
        self.public = "public"
        self.value = value

    def method(self, arg: Any = None) -> str:
        return f"method called with {arg}"

    @property
    def prop(self) -> str:
        return "property value"


class ContainerClass:
    def __init__(self):
        self.list = [1, 2, 3]
        self.dict = {"a": 1, "b": 2}
        self.set = {1, 2, 3}

    def __getitem__(self, key):
        return self.dict[key]

    def __setitem__(self, key, value):
        self.dict[key] = value

    def __delitem__(self, key):
        del self.dict[key]


@pytest.fixture
def simple_object():
    return SimpleDataClass(name="test", value=42)


@pytest.fixture
def test_object():
    return TestClass()


@pytest.fixture
def container_object():
    return ContainerClass()


@pytest.fixture
def test_list():
    return [1, 2, 3]


@pytest.fixture
def test_dict():
    return {"a": 1, "b": 2, "c": 3}


@pytest.fixture
def test_set():
    return {1, 2, 3}
