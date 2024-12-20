import pytest
from typing import Dict, Any
from unittest.mock import Mock
from pypaya_python_tools.class_instantiation import ClassInstanceFactory
from pypaya_python_tools.class_instantiation.specialized_factory import (
    FactoryCreationError,
    FactoryValidationError,
    SpecializedFactory
)
from tests.class_instantiation.test_package.implementations import (
    TestBaseClass,
    TestImplementation,
    SpecialImplementation
)


class TestFactory(SpecializedFactory[TestBaseClass]):
    def _initialize_type_mapping(self) -> None:
        self.type_mapping = {
            "TestImplementation": "tests.class_instantiation.test_package.implementations",
            "SpecialImplementation": "tests.class_instantiation.test_package.implementations"
        }

    def _initialize_special_handlers(self) -> None:
        self.special_handlers = {
            "SpecialCase": self._handle_special_case
        }

    def _handle_special_case(self, config: Dict[str, Any]) -> TestBaseClass:
        return TestImplementation(value=config.get("value", "special"))


# Test factory for testing initialization validation
class EmptyTestFactory(SpecializedFactory[TestBaseClass]):
    def _initialize_type_mapping(self) -> None:
        pass


# Fixtures
@pytest.fixture
def factory():
    return TestFactory(base_class=TestBaseClass)


@pytest.fixture
def factory_no_custom():
    return TestFactory(base_class=TestBaseClass, allow_custom=False)


@pytest.fixture
def mock_class_instance_factory():
    return Mock(spec=ClassInstanceFactory)


# Initialization tests
def test_factory_initialization():
    """Test factory initialization with different parameters."""
    # Basic initialization
    factory = TestFactory()
    assert factory.allow_custom is True
    assert factory.base_class is None

    # With base class
    factory = TestFactory(base_class=TestBaseClass)
    assert factory.base_class == TestBaseClass

    # With custom disabled
    factory = TestFactory(allow_custom=False)
    assert factory.allow_custom is False


def test_empty_type_mapping():
    """Test that factory raises error when no types are mapped."""
    with pytest.raises(ValueError) as exc_info:
        EmptyTestFactory()
    assert "must define at least one type mapping" in str(exc_info.value)


# Basic creation tests
def test_basic_creation(factory):
    """Test basic object creation."""
    obj = factory.build({
        "class_name": "TestImplementation",
        "value": "test"
    })
    assert isinstance(obj, TestImplementation)
    assert obj.value == "test"


def test_explicit_args_kwargs(factory):
    """Test creation with explicit args and kwargs."""
    obj = factory.build({
        "class_name": "TestImplementation",
        "args": [],
        "kwargs": {"value": "test"}
    })
    assert isinstance(obj, TestImplementation)
    assert obj.value == "test"


def test_special_implementation(factory):
    """Test creation of special implementation."""
    obj = factory.build({
        "class_name": "SpecialImplementation",
        "special_value": "special_test"
    })
    assert isinstance(obj, SpecialImplementation)
    assert obj.special_value == "special_test"


# Special handler tests
def test_special_handler(factory):
    """Test special case handling."""
    obj = factory.build({
        "class_name": "SpecialCase",
        "value": "custom_special"
    })
    assert isinstance(obj, TestImplementation)
    assert obj.value == "custom_special"


def test_special_handler_default_value(factory):
    """Test special handler with default value."""
    obj = factory.build({
        "class_name": "SpecialCase"
    })
    assert isinstance(obj, TestImplementation)
    assert obj.value == "special"


# Custom implementation tests
def test_custom_implementation(factory):
    """Test custom implementation creation."""
    obj = factory.build({
        "class_name": "TestImplementation",
        "module": "tests.class_instantiation.test_package.implementations",
        "value": "custom"
    })
    assert isinstance(obj, TestImplementation)
    assert obj.value == "custom"


def test_custom_implementation_disabled(factory_no_custom):
    """Test that custom implementations are properly disabled."""
    with pytest.raises(FactoryValidationError) as exc_info:
        factory_no_custom.build({
            "class_name": "TestImplementation",
            "module": "tests.class_instantiation.test_package.implementations",
            "value": "custom"
        })
    assert "Custom implementations not allowed" in str(exc_info.value)


# Error handling tests
def test_unknown_type(factory):
    """Test error handling for unknown types."""
    with pytest.raises(FactoryValidationError) as exc_info:
        factory.build({
            "class_name": "UnknownType"
        })
    assert "Unknown class: UnknownType" in str(exc_info.value)
    assert "Available types:" in str(exc_info.value)


def test_missing_class_name(factory):
    """Test error handling for missing class_name."""
    with pytest.raises(FactoryValidationError) as exc_info:
        factory.build({})
    assert "must include 'class_name'" in str(exc_info.value)


def test_invalid_base_class(factory):
    """Test base class validation."""
    class NotBaseClass:
        pass

    with pytest.raises(FactoryValidationError) as exc_info:
        invalid_instance = NotBaseClass()
        factory._validate_instance(invalid_instance)
    assert f"expected {TestBaseClass.__name__}" in str(exc_info.value)


def test_factory_creation_error(factory):
    """Test general creation error handling."""
    with pytest.raises(FactoryCreationError) as exc_info:
        factory.build({
            "class_name": "TestImplementation",
            "module": "nonexistent.module"
        })
    assert "Failed to create instance" in str(exc_info.value)


# Multiple instance creation tests
def test_build_many(factory):
    """Test building multiple instances."""
    configs = [
        {"class_name": "TestImplementation", "value": "test1"},
        {"class_name": "TestImplementation", "value": "test2"}
    ]
    objects = factory.build_many(configs)
    assert len(objects) == 2
    assert all(isinstance(obj, TestImplementation) for obj in objects)
    assert [obj.value for obj in objects] == ["test1", "test2"]


def test_build_many_mixed_types(factory):
    """Test building multiple instances of different types."""
    configs = [
        {"class_name": "TestImplementation", "value": "test"},
        {"class_name": "SpecialImplementation", "special_value": "special"}
    ]
    objects = factory.build_many(configs)
    assert len(objects) == 2
    assert isinstance(objects[0], TestImplementation)
    assert isinstance(objects[1], SpecialImplementation)
    assert objects[0].value == "test"
    assert objects[1].special_value == "special"


# Type registration tests
def test_register_unregister_type(factory):
    """Test registering and unregistering types."""
    # Register new type
    factory.register_type("NewType", "module.path.NewType")
    assert "NewType" in factory.type_mapping

    # Unregister type
    factory.unregister_type("NewType")
    assert "NewType" not in factory.type_mapping


def test_invalid_type_registration(factory):
    """Test error handling for invalid type registration."""
    with pytest.raises(ValueError):
        factory.register_type(123, "path")  # Invalid name type
    with pytest.raises(ValueError):
        factory.register_type("name", 123)  # Invalid path type


def test_unregister_nonexistent_type(factory):
    """Test unregistering a type that doesn't exist."""
    original_mapping = factory.type_mapping.copy()
    factory.unregister_type("NonexistentType")
    assert factory.type_mapping == original_mapping


def test_register_existing_type(factory):
    """Test registering a type that already exists."""
    original_module = factory.type_mapping["TestImplementation"]
    factory.register_type("TestImplementation", "new.module.path")
    assert factory.type_mapping["TestImplementation"] == "new.module.path"
    assert factory.type_mapping["TestImplementation"] != original_module
