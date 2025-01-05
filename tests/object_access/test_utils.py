from dataclasses import dataclass
import pytest
from pypaya_python_tools.object_access.exceptions import InstantiationError
from pypaya_python_tools.object_access.utils import (
    instantiate_class,
    call,
    get_attribute,
    set_attribute,
    configure_object,
    import_and_instantiate,
    import_and_call,
    create_instance
)


# Test Classes and Functions
class SimpleClass:
    def __init__(self, value: str = "default"):
        self.value = value

    def method(self, x: int) -> int:
        return x + 1


@dataclass
class DataClass:
    name: str
    value: int


class ComplexClass:
    def __init__(self, nested: SimpleClass):
        self.nested = nested

    @property
    def prop(self) -> str:
        return "property"


def simple_function(x: int, y: int = 0) -> int:
    return x + y


# Test instantiate_class
def test_instantiate_class_basic():
    obj = instantiate_class(SimpleClass, "test")
    assert isinstance(obj, SimpleClass)
    assert obj.value == "test"


def test_instantiate_class_with_defaults():
    obj = instantiate_class(SimpleClass)
    assert obj.value == "default"


def test_instantiate_class_with_kwargs():
    obj = instantiate_class(SimpleClass, value="test")
    assert obj.value == "test"


def test_instantiate_class_dataclass():
    obj = instantiate_class(DataClass, "test", 42)
    assert obj.name == "test"
    assert obj.value == 42


def test_instantiate_class_invalid_args():
    with pytest.raises(InstantiationError):
        instantiate_class(SimpleClass, 1, 2, 3)  # too many arguments


# Test call
def test_call_function():
    assert call(simple_function, 1) == 1
    assert call(simple_function, 1, y=2) == 3


def test_call_method():
    obj = SimpleClass()
    assert call(obj.method, 41) == 42


def test_call_lambda():
    func = lambda x, y: x * y
    assert call(func, 6, 7) == 42


def test_call_invalid():
    with pytest.raises(Exception):
        call(SimpleClass(), 1)  # object is not callable


# Test attribute access
def test_get_attribute_basic():
    obj = SimpleClass("test")
    assert get_attribute(obj, "value") == "test"


def test_get_attribute_property():
    obj = ComplexClass(SimpleClass())
    assert get_attribute(obj, "prop") == "property"


def test_get_attribute_nested():
    inner = SimpleClass("inner")
    outer = ComplexClass(inner)
    assert get_attribute(get_attribute(outer, "nested"), "value") == "inner"


def test_get_attribute_missing():
    obj = SimpleClass()
    with pytest.raises(AttributeError):
        get_attribute(obj, "missing")


def test_set_attribute_basic():
    obj = SimpleClass()
    set_attribute(obj, "value", "new")
    assert obj.value == "new"


def test_set_attribute_new():
    obj = SimpleClass()
    set_attribute(obj, "new_attr", 42)
    assert obj.new_attr == 42


def test_set_attribute_type_change():
    obj = SimpleClass("string")
    set_attribute(obj, "value", 42)
    assert obj.value == 42


# Test configure_object
def test_configure_object_basic():
    obj = SimpleClass()
    configure_object(obj, {"value": "new"})
    assert obj.value == "new"


def test_configure_object_multiple():
    obj = SimpleClass()
    configure_object(obj, {
        "value": "new",
        "extra": 42,
        "more": [1, 2, 3]
    })
    assert obj.value == "new"
    assert obj.extra == 42
    assert obj.more == [1, 2, 3]


def test_configure_object_empty():
    obj = SimpleClass()
    original_value = obj.value
    configure_object(obj, {})
    assert obj.value == original_value


# Test create_instance
def test_create_instance_basic():
    config = {
        "module": "tests.object_access.test_utils",
        "class": "SimpleClass",
        "kwargs": {"value": "test"}
    }
    obj = create_instance(config)
    assert isinstance(obj, SimpleClass)
    assert obj.value == "test"


def test_create_instance_nested():
    config = {
        "module": "tests.object_access.test_utils",
        "class": "ComplexClass",
        "kwargs": {
            "nested": {
                "module": "tests.object_access.test_utils",
                "class": "SimpleClass",
                "kwargs": {"value": "inner"}
            }
        }
    }
    obj = create_instance(config)
    assert isinstance(obj, ComplexClass)
    assert isinstance(obj.nested, SimpleClass)
    assert obj.nested.value == "inner"


def test_create_instance_list():
    config = [
        {
            "module": "tests.object_access.test_utils",
            "class": "SimpleClass",
            "kwargs": {"value": "one"}
        },
        {
            "module": "tests.object_access.test_utils",
            "class": "SimpleClass",
            "kwargs": {"value": "two"}
        }
    ]
    objects = create_instance(config)
    assert len(objects) == 2
    assert all(isinstance(obj, SimpleClass) for obj in objects)
    assert objects[0].value == "one"
    assert objects[1].value == "two"


def test_create_instance_invalid():
    # Missing both module and file
    with pytest.raises(ValueError, match="Must provide either 'module' or 'file'"):
        create_instance({
            "class": "SimpleClass",
            "args": []
        })

    # Invalid args type
    with pytest.raises(ValueError, match="'args' must be a list"):
        create_instance({
            "module": "tests.object_access.test_utils",
            "class": "SimpleClass",
            "args": "not_a_list"
        })

    # Invalid kwargs type
    with pytest.raises(ValueError, match="'kwargs' must be a dictionary"):
        create_instance({
            "module": "tests.object_access.test_utils",
            "class": "SimpleClass",
            "kwargs": "not_a_dict"
        })

    # Invalid class name type
    with pytest.raises(ValueError, match="'class' must be a string"):
        create_instance({
            "module": "tests.object_access.test_utils",
            "class": 123,  # should be string
        })


# Test import utilities
def test_import_and_instantiate():
    obj = import_and_instantiate(
        "tests.object_access.test_utils",
        "SimpleClass",
        value="imported"
    )
    assert isinstance(obj, SimpleClass)
    assert obj.value == "imported"


def test_import_and_call():
    result = import_and_call(
        "tests.object_access.test_utils",
        "simple_function",
        40,
        y=2
    )
    assert result == 42
