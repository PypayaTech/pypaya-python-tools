import sys
import pytest
from typing import Dict, Any
from pypaya_python_tools.create_from_config.config_driven_factory import ConfigDrivenFactory, FactoryConfig, FactoryConfigError


# Test fixtures and helper classes
class DummyBase:
    """Base class for testing"""
    pass


class DummyImplementation(DummyBase):
    """Simple implementation for testing"""

    def __init__(self, param1=None, param2=None):
        self.param1 = param1
        self.param2 = param2


class TestFactory(ConfigDrivenFactory[DummyBase]):
    """Test implementation of ConfigDrivenFactory"""

    def __init__(self, allow_custom=True):
        super().__init__(base_class=DummyBase, allow_custom=allow_custom)

    def _initialize_type_mapping(self) -> None:
        self.type_mapping = {
            "DummyImplementation": "tests.create_from_config.test_config_driven_factory"
        }

    def _initialize_special_handlers(self) -> None:
        self.special_handlers = {
            "SpecialCase": self._handle_special_case
        }

    def _handle_special_case(self, config: Dict[str, Any]) -> DummyBase:
        return DummyImplementation(**config)


@pytest.fixture
def factory():
    return TestFactory()


# Test initialization and setup
def test_factory_initialization():
    """Test basic factory initialization"""
    factory = TestFactory()
    assert factory.base_class == DummyBase
    assert factory.allow_custom is True
    assert "DummyImplementation" in factory.type_mapping


def test_factory_no_type_mapping():
    """Test factory initialization without type mapping"""

    class EmptyFactory(ConfigDrivenFactory):
        def _initialize_type_mapping(self) -> None:
            pass

    with pytest.raises(ValueError):
        EmptyFactory()


# Test configuration normalization
def test_config_normalization_explicit_format(factory):
    """Test normalization of explicit args/kwargs format"""
    config = {
        "class_name": "TestClass",
        "args": [1, 2],
        "kwargs": {"param": "value"},
        "module": "test_module"
    }
    normalized = factory._normalize_config(config)
    assert isinstance(normalized, FactoryConfig)
    assert normalized.class_name == "TestClass"
    assert normalized.args == [1, 2]
    assert normalized.kwargs == {"param": "value"}
    assert normalized.module == "test_module"


def test_config_normalization_flat_format(factory):
    """Test normalization of flat configuration format"""
    config = {
        "class_name": "TestClass",
        "param1": "value1",
        "param2": "value2"
    }
    normalized = factory._normalize_config(config)
    assert normalized.class_name == "TestClass"
    assert normalized.kwargs == {"param1": "value1", "param2": "value2"}
    assert normalized.args == []


def test_config_normalization_missing_class_name(factory):
    """Test handling of missing class_name in configuration"""
    with pytest.raises(FactoryConfigError):
        factory._normalize_config({})


# Test instance creation
def test_build_with_known_type(monkeypatch, factory):
    """Test building instance of known type"""

    # Mock create_instance to return a DummyImplementation
    def mock_create_instance(config):
        return DummyImplementation()

    monkeypatch.setattr("pypaya_python_tools.create_from_config.core.create_instance",
                        mock_create_instance)

    instance = factory.build({"class_name": "DummyImplementation"})
    assert isinstance(instance, DummyImplementation)


def test_build_with_special_handler(factory):
    """Test building instance using special handler"""
    config = {
        "class_name": "SpecialCase",
        "param1": "test",
        "param2": 123
    }
    instance = factory.build(config)
    assert isinstance(instance, DummyImplementation)
    assert instance.param1 == "test"
    assert instance.param2 == 123


def test_build_with_unknown_type(factory):
    """Test handling of unknown type"""
    with pytest.raises(FactoryConfigError):
        factory.build({"class_name": "UnknownType"})


def test_build_custom_implementation_when_not_allowed():
    """Test handling of custom implementation when not allowed"""
    factory = TestFactory(allow_custom=False)
    config = {
        "class_name": "CustomClass",
        "module": "custom_module"
    }
    with pytest.raises(FactoryConfigError):
        factory.build(config)


# Test validation
def test_instance_validation(factory):
    """Test instance validation against base class"""

    class NotDummyBase:
        pass

    with pytest.raises(FactoryConfigError):
        factory._validate_instance(NotDummyBase())


def test_build_with_invalid_config_format(factory):
    """Test handling of invalid configuration format"""
    with pytest.raises(FactoryConfigError):
        factory.build(None)

    with pytest.raises(FactoryConfigError):
        factory.build("not_a_dict")


# Test custom implementation handling
def test_custom_implementation_from_module(tmp_path, factory):
    """Test creating instance from custom module"""
    # Create a temporary module with a class that inherits from DummyBase
    module_path = tmp_path / "custom_module.py"
    module_content = """
from tests.create_from_config.test_config_driven_factory import DummyBase

class CustomClass(DummyBase):
    def __init__(self, param1=None):
        self.param1 = param1
"""
    module_path.write_text(module_content)

    # Add module directory to Python path
    sys.path.insert(0, str(tmp_path))

    try:
        config = {
            "class_name": "CustomClass",
            "module": "custom_module",
            "param1": "test"
        }
        instance = factory.build(config)

        assert isinstance(instance, DummyBase)  # Verify inheritance
        assert instance.param1 == "test"

    finally:
        # Clean up: remove the temporary directory from Python path
        sys.path.pop(0)


def test_custom_implementation_from_file(tmp_path, factory):
    """Test creating instance from custom file"""
    # Create a temporary Python file with a class that inherits from DummyBase
    file_path = tmp_path / "custom_file.py"
    file_content = """
from tests.create_from_config.test_config_driven_factory import DummyBase

class CustomClass(DummyBase):
    def __init__(self, param1=None):
        self.param1 = param1
"""
    file_path.write_text(file_content)

    config = {
        "class_name": "CustomClass",
        "file": str(file_path),
        "param1": "test"
    }
    instance = factory.build(config)

    assert isinstance(instance, DummyBase)  # Verify inheritance
    assert instance.param1 == "test"


def test_parameter_validation():
    """Test parameter type validation and conversion"""

    class ValidatedClass(DummyBase):
        def __init__(self, int_param: int, str_param: str, optional_param: float = 1.0):
            self.int_param = int_param
            self.str_param = str_param
            self.optional_param = optional_param

    class ValidationFactory(TestFactory):
        def _initialize_type_mapping(self) -> None:
            self.type_mapping = {
                "ValidatedClass": "tests.create_from_config.test_config_driven_factory"
            }

    # Temporarily add ValidatedClass to the module's globals
    import sys
    current_module = sys.modules[__name__]
    setattr(current_module, "ValidatedClass", ValidatedClass)

    factory = ValidationFactory()
    factory._class_info_cache["ValidatedClass"] = factory._get_class_info(ValidatedClass)

    try:
        # Test valid parameters with type conversion
        instance = factory.build({
            "class_name": "ValidatedClass",
            "int_param": "123",  # Should be converted to int
            "str_param": "test"
        })
        assert instance.int_param == 123
        assert instance.str_param == "test"
        assert instance.optional_param == 1.0  # Default value

        # Test missing required parameter
        with pytest.raises(FactoryConfigError, match="Missing required parameter"):
            factory.build({
                "class_name": "ValidatedClass",
                "str_param": "test"
            })

        # Test invalid type that can't be converted
        with pytest.raises(FactoryConfigError, match="Invalid type"):
            factory.build({
                "class_name": "ValidatedClass",
                "int_param": "not_an_int",
                "str_param": "test"
            })
    finally:
        # Clean up: remove the temporary class
        delattr(current_module, "ValidatedClass")


def test_parameter_documentation():
    """Test extraction and use of parameter documentation"""

    class DocumentedClass(DummyBase):
        def __init__(self, param1: str):
            """
            :param param1: This is a documented parameter
            """
            self.param1 = param1

    class DocFactory(TestFactory):
        def _initialize_type_mapping(self) -> None:
            self.type_mapping = {
                "DocumentedClass": "tests.create_from_config.test_config_driven_factory"
            }

    # Temporarily add DocumentedClass to the module's globals
    import sys
    current_module = sys.modules[__name__]
    setattr(current_module, 'DocumentedClass', DocumentedClass)

    factory = DocFactory()
    factory._class_info_cache["DocumentedClass"] = factory._get_class_info(DocumentedClass)

    try:
        class_info = factory._class_info_cache["DocumentedClass"]
        assert class_info.parameters["param1"].doc == "This is a documented parameter"
    finally:
        # Clean up: remove the temporary class
        delattr(current_module, 'DocumentedClass')


def test_default_value_handling():
    """Test handling of default parameter values"""

    class DefaultsClass(DummyBase):
        def __init__(self, required_param: str, optional_param: int = 42):
            self.required_param = required_param
            self.optional_param = optional_param

    class DefaultsFactory(TestFactory):
        def _initialize_type_mapping(self) -> None:
            self.type_mapping = {
                "DefaultsClass": "tests.create_from_config.test_config_driven_factory"
            }

    # Temporarily add DefaultsClass to the module's globals
    import sys
    current_module = sys.modules[__name__]
    setattr(current_module, 'DefaultsClass', DefaultsClass)

    factory = DefaultsFactory()
    factory._class_info_cache["DefaultsClass"] = factory._get_class_info(DefaultsClass)

    try:
        instance = factory.build({
            "class_name": "DefaultsClass",
            "required_param": "test"
        })
        assert instance.optional_param == 42  # Default value should be applied
    finally:
        # Clean up: remove the temporary class
        delattr(current_module, 'DefaultsClass')
