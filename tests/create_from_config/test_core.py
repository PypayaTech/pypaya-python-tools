import pytest
from datetime import datetime
from pypaya_python_tools.create_from_config import create_instance, ValidationError, InstantiationError
from tests.create_from_config.fixtures.test_classes import SimpleClass, ComplexClass, AbstractClass, NonDataClass


def test_create_instance_basic():
    config = {
        "module": "datetime",
        "class": "datetime",
        "args": [2023, 6, 15],
        "kwargs": {"hour": 10, "minute": 30}
    }
    obj = create_instance(config)
    assert isinstance(obj, datetime)
    assert obj.year == 2023
    assert obj.hour == 10


def test_create_instance_dataclass():
    config = {
        "module": "tests.create_from_config.fixtures.test_classes",
        "class": "SimpleClass",
        "kwargs": {"value": "test"}
    }
    obj = create_instance(config)
    assert isinstance(obj, SimpleClass)
    assert obj.value == "test"


def test_create_instance_nested():
    config = {
        "module": "tests.create_from_config.fixtures.test_classes",
        "class": "ComplexClass",
        "kwargs": {
            "nested": {
                "module": "tests.create_from_config.fixtures.test_classes",
                "class": "SimpleClass",
                "kwargs": {"value": "inner"}
            },
            "optional": "test"
        }
    }
    obj = create_instance(config)
    assert isinstance(obj, ComplexClass)
    assert isinstance(obj.nested, SimpleClass)
    assert obj.nested.value == "inner"
    assert obj.optional == "test"


def test_create_instance_list():
    config = [
        {
            "module": "tests.create_from_config.fixtures.test_classes",
            "class": "SimpleClass",
            "kwargs": {"value": "one"}
        },
        {
            "module": "tests.create_from_config.fixtures.test_classes",
            "class": "SimpleClass",
            "kwargs": {"value": "two"}
        }
    ]
    objects = create_instance(config)
    assert len(objects) == 2
    assert all(isinstance(obj, SimpleClass) for obj in objects)
    assert objects[0].value == "one"
    assert objects[1].value == "two"


def test_create_instance_from_file(tmp_path):
    module_content = """
class TestClass:
    def __init__(self, value):
        self.value = value
"""
    test_file = tmp_path / "test_module.py"
    test_file.write_text(module_content)

    config = {
        "file": str(test_file),
        "class": "TestClass",
        "args": ["test_value"]
    }
    obj = create_instance(config)
    assert obj.value == "test_value"


def test_create_instance_validation():
    config = {
        "module": "tests.create_from_config.fixtures.test_classes",
        "class": "SimpleClass",
        "kwargs": {"value": "test"}
    }
    obj = create_instance(config, expected_type=SimpleClass)
    assert isinstance(obj, SimpleClass)

    with pytest.raises(ValidationError):
        create_instance(config, expected_type=ComplexClass)


def test_create_instance_abstract():
    config = {
        "module": "tests.create_from_config.fixtures.test_classes",
        "class": "AbstractClass"
    }
    with pytest.raises(InstantiationError, match="Cannot instantiate abstract class"):
        create_instance(config)


def test_create_instance_non_dataclass():
    config = {
        "module": "tests.create_from_config.fixtures.test_classes",
        "class": "NonDataClass",
        "args": [1, 2]
    }
    obj = create_instance(config)
    assert isinstance(obj, NonDataClass)
    assert obj.x == 1
    assert obj.y == 2
