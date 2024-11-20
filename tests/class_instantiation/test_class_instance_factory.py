import pytest
from collections import OrderedDict
from datetime import datetime, date, time
from pypaya_python_tools.imports.dynamic_importer import DynamicImporter, ImportConfig
from pypaya_python_tools.class_instantiation import ClassInstanceFactory


@pytest.fixture
def generator():
    importer = DynamicImporter(ImportConfig())
    return ClassInstanceFactory(importer)


def test_create_simple_object(generator):
    config = {
        "module": "datetime",
        "class": "datetime",
        "args": [2023, 5, 17],
        "kwargs": {"hour": 14, "minute": 30}
    }
    result = generator.create(config)
    assert isinstance(result, datetime)
    assert result == datetime(2023, 5, 17, 14, 30)


def test_create_date_object(generator):
    config = {
        "module": "datetime",
        "class": "date",
        "args": [2023, 5, 17]
    }
    result = generator.create(config)
    assert isinstance(result, date)
    assert result == date(2023, 5, 17)


def test_create_time_object(generator):
    config = {
        "module": "datetime",
        "class": "time",
        "args": [14, 30]
    }
    result = generator.create(config)
    assert isinstance(result, time)
    assert result == time(14, 30)


def test_create_nested_object(generator):
    config = {
        "module": "collections",
        "class": "namedtuple",
        "args": ["Person", "name age"],
        "kwargs": {
            "defaults": [
                {
                    "module": "datetime",
                    "class": "date",
                    "args": [1990, 1, 1]
                }
            ]
        }
    }
    Person = generator.create(config)
    john = Person("John")
    assert john.name == "John"
    assert isinstance(john.age, date)
    assert john.age == date(1990, 1, 1)


def test_create_multiple_objects(generator):
    config = [
        {"module": "datetime", "class": "date", "args": [2023, 5, 17]},
        {"module": "datetime", "class": "time", "args": [14, 30]}
    ]
    results = generator.create(config)
    assert len(results) == 2
    assert results[0] == date(2023, 5, 17)
    assert results[1] == time(14, 30)


def test_invalid_config(generator):
    config = {"class": "datetime"}
    with pytest.raises(ValueError, match="Configuration must include a 'module' key"):
        generator.create(config)


def test_import_error(generator):
    config = {"module": "non_existent_module"}
    with pytest.raises(ImportError):
        generator.create(config)


def test_nested_module_import(generator):
    config = {
        "module": "datetime",
        "class": "datetime",
        "args": [2023, 5, 17, 14, 30]
    }
    result = generator.create(config)
    assert isinstance(result, datetime)
    assert result.year == 2023
    assert result.month == 5
    assert result.day == 17
    assert result.hour == 14
    assert result.minute == 30


def test_nested_class_import(generator):
    config = {
        "module": "collections",
        "class": "OrderedDict",
        "args": [{"a": 1, "b": 2, "c": 3}]
    }
    result = generator.create(config)
    assert isinstance(result, OrderedDict)
    assert list(result.keys()) == ["a", "b", "c"]
    assert list(result.values()) == [1, 2, 3]


def test_nested_object_creation(generator):
    config = {
        "module": "collections",
        "class": "namedtuple",
        "args": ["Person", "name age"],
        "kwargs": {
            "defaults": [
                {
                    "module": "datetime",
                    "class": "date",
                    "args": [1990, 1, 1]
                }
            ]
        }
    }
    Person = generator.create(config)
    john = Person("John")
    assert john.name == "John"
    assert isinstance(john.age, date)
    assert john.age.year == 1990
    assert john.age.month == 1
    assert john.age.day == 1


def test_abstract_class_exception(generator):
    config = {
        "module": "collections.abc",
        "class": "Sequence"
    }
    with pytest.raises(ValueError, match="Cannot instantiate abstract class: Sequence"):
        generator.create(config)


if __name__ == "__main__":
    pytest.main()
