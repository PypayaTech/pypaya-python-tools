import pytest
from datetime import datetime
from pypaya_python_tools.create_from_config import create_instance, ValidationError, InstantiationError, \
    create_callable, CallableCreationError
from pypaya_python_tools.importing import ImportSecurity
from tests.create_from_config.fixtures.test_classes import SimpleClass, ComplexClass, AbstractClass, NonDataClass


class TestCreateInstance:
    def test_create_instance_basic(self):
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

    def test_create_instance_dataclass(self):
        config = {
            "module": "tests.create_from_config.fixtures.test_classes",
            "class": "SimpleClass",
            "kwargs": {"value": "test"}
        }
        obj = create_instance(config)
        assert isinstance(obj, SimpleClass)
        assert obj.value == "test"

    def test_create_instance_nested(self):
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

    def test_create_instance_list(self):
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

    def test_create_instance_from_file(self, tmp_path):
        module_content = """
class TestClass:
    def __init__(self, value):
        self.value = value
"""
        test_file = tmp_path / "test_module.py"
        test_file.write_text(module_content)

        # Test with explicit file path
        config = {
            "file": str(test_file),
            "class": "TestClass",
            "args": ["test_value"]
        }
        obj = create_instance(config)
        assert obj.value == "test_value"

    def test_create_instance_security(self):
        # Test with custom security settings
        config = {
            "module": "datetime",
            "class": "datetime",
            "args": [2023, 6, 15]
        }

        # Default security allows imports
        obj = create_instance(config)
        assert isinstance(obj, datetime)

        # Custom security can block imports
        security = ImportSecurity(enabled=True, blocked_modules={"datetime"})
        with pytest.raises(InstantiationError):
            create_instance(config, security=security)

        # Disabled security allows all imports
        security_disabled = ImportSecurity(enabled=False)
        obj = create_instance(config, security=security_disabled)
        assert isinstance(obj, datetime)

    def test_create_instance_validation(self):
        config = {
            "module": "tests.create_from_config.fixtures.test_classes",
            "class": "SimpleClass",
            "kwargs": {"value": "test"}
        }
        obj = create_instance(config, expected_type=SimpleClass)
        assert isinstance(obj, SimpleClass)

        with pytest.raises(ValidationError):
            create_instance(config, expected_type=ComplexClass)

    def test_create_instance_abstract(self):
        config = {
            "module": "tests.create_from_config.fixtures.test_classes",
            "class": "AbstractClass"
        }
        with pytest.raises(InstantiationError, match="Cannot instantiate abstract class"):
            create_instance(config)

    def test_create_instance_non_dataclass(self):
        config = {
            "module": "tests.create_from_config.fixtures.test_classes",
            "class": "NonDataClass",
            "args": [1, 2]
        }
        obj = create_instance(config)
        assert isinstance(obj, NonDataClass)
        assert obj.x == 1
        assert obj.y == 2

    def test_create_instance_invalid_configs(self):
        with pytest.raises(ValidationError, match="Must provide either 'module' or 'file'"):
            create_instance({"class": "TestClass"})

        with pytest.raises(ValidationError, match="'args' must be a list"):
            create_instance({
                "module": "datetime",
                "class": "datetime",
                "args": "not_a_list"
            })

        with pytest.raises(ValidationError, match="'kwargs' must be a dictionary"):
            create_instance({
                "module": "datetime",
                "class": "datetime",
                "kwargs": "not_a_dict"
            })

    def test_create_instance_not_a_class(self):
        config = {
            "module": "math",
            "class": "sqrt"
        }
        with pytest.raises(InstantiationError, match="'sqrt' is not a class"):
            create_instance(config)


class TestCreateCallable:
    def test_create_callable_function_from_module(self):
        config = {
            "module": "math",
            "name": "sqrt"
        }
        func = create_callable(config)
        assert callable(func)
        assert func(4) == 2.0

    def test_create_callable_function_from_file(self):
        # Create a temporary file with a function
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f:
            f.write("""
def test_function(x):
    return x * 2
""")
            temp_file = f.name

        try:
            config = {
                "file": temp_file,
                "name": "test_function"
            }
            func = create_callable(config)
            assert callable(func)
            assert func(5) == 10
        finally:
            os.unlink(temp_file)

    def test_create_callable_class_with_call(self):
        config = {
            "class": {
                "module": "tests.create_from_config.fixtures.test_classes",
                "class": "CallableClass",
                "kwargs": {"factor": 2}
            }
        }
        func = create_callable(config)
        assert callable(func)
        assert func(5) == 10

    def test_create_callable_instance_method(self):
        config = {
            "class": {
                "module": "tests.create_from_config.fixtures.test_classes",
                "class": "Calculator"
            },
            "method": "add"
        }
        func = create_callable(config)
        assert callable(func)
        assert func(2, 3) == 5

    def test_create_callable_partial(self):
        config = {
            "partial": {
                "function": {
                    "module": "operator",
                    "name": "add"
                },
                "args": [1]
            }
        }
        func = create_callable(config)
        assert callable(func)
        assert func(5) == 6

    def test_create_callable_nested(self):
        config = {
            "partial": {
                "function": {
                    "class": {
                        "module": "tests.create_from_config.fixtures.test_classes",
                        "class": "Calculator"
                    },
                    "method": "add"
                },
                "args": [10]
            }
        }
        func = create_callable(config)
        assert callable(func)
        assert func(5) == 15

    def test_create_callable_errors(self):
        # Non-callable object
        config = {
            "module": "sys",
            "name": "path"
        }
        with pytest.raises(CallableCreationError, match="not callable"):
            create_callable(config)

        # Non-existent method
        config = {
            "class": {
                "module": "tests.create_from_config.fixtures.test_classes",
                "class": "SimpleClass",
                "kwargs": {"value": "test"}
            },
            "method": "nonexistent_method"
        }
        with pytest.raises(CallableCreationError):
            create_callable(config)

        # Invalid configuration
        with pytest.raises(ValidationError, match="Invalid callable configuration"):
            create_callable({"invalid": "config"})

        # Invalid partial configuration
        with pytest.raises(ValidationError, match="must contain 'function'"):
            create_callable({"partial": "not_a_dict"})
