from abc import ABC, abstractmethod
import pytest
from dataclasses import dataclass
from typing import Any
from pypaya_python_tools.object_access.security import ObjectAccessSecurityContext, STRICT_OBJECT_ACCESS_SECURITY
from pypaya_python_tools.object_access.definitions import AccessType, ObjectAccess
from pypaya_python_tools.object_access.exceptions import (
    InstantiationError,
    CallError,
    ObjectAccessSecurityError
)
from pypaya_python_tools.object_access.handlers.direct import DirectHandler
from pypaya_python_tools.object_access.handlers.instantiate import InstantiateHandler
from pypaya_python_tools.object_access.handlers.call import CallHandler
from pypaya_python_tools.object_access.handlers.attribute import AttributeHandler


# Test classes
@dataclass
class TestClass:
    value: Any = None

    def method(self, arg):
        return f"Method called with {arg}"


class AbstractClass(ABC):
    @abstractmethod
    def abstract_method(self):
        pass


class NonABCAbstractClass:
    """Abstract class without inheriting from ABC."""
    @abstractmethod
    def abstract_method(self):
        pass


class MixinWithAbstractMethod:
    """Mixin class with abstract method."""
    @abstractmethod
    def mixin_method(self):
        pass


class ConcreteClass:
    """Regular concrete class."""
    def method(self):
        pass


class ChildWithoutImpl(NonABCAbstractClass):
    """Child class that doesn't implement abstract method."""
    pass


class ConcreteImplementation(NonABCAbstractClass):
    """Concrete class that implements abstract method."""
    def abstract_method(self):
        return "implemented"



class TestDirectHandler:
    @pytest.fixture
    def handler(self):
        return DirectHandler(ObjectAccessSecurityContext())

    def test_can_handle(self, handler):
        access = ObjectAccess(AccessType.DIRECT)
        assert handler.can_handle(42, access)
        assert handler.can_handle("string", access)
        assert handler.can_handle(None, access)
        assert handler.can_handle(object(), access)

    def test_handle_various_types(self, handler):
        access = ObjectAccess(AccessType.DIRECT)

        # Test with different types
        test_cases = [
            42,
            "string",
            [1, 2, 3],
            {"key": "value"},
            None,
            object()
        ]

        for obj in test_cases:
            result = handler.handle(obj, access)
            assert result.value is obj  # Direct access should return the same object
            assert result.metadata["type"] == type(obj).__name__

    def test_handle_complex_objects(self, handler):
        class TestClass:
            def __init__(self):
                self.value = "test"

        obj = TestClass()
        access = ObjectAccess(AccessType.DIRECT)
        result = handler.handle(obj, access)
        assert result.value is obj
        assert result.metadata["type"] == "TestClass"


class TestInstantiateHandler:
    @pytest.fixture
    def handler(self):
        return InstantiateHandler(ObjectAccessSecurityContext())

    def test_can_handle(self, handler):
        access = ObjectAccess(AccessType.INSTANTIATE)
        assert handler.can_handle(TestClass, access)
        assert not handler.can_handle(lambda x: x, access)

    def test_successful_instantiation(self, handler):
        access = ObjectAccess(
            AccessType.INSTANTIATE,
            args=("test_value",)
        )
        result = handler.handle(TestClass, access)
        assert isinstance(result.value, TestClass)
        assert result.value.value == "test_value"
        assert result.metadata["class"] == TestClass

    def test_abstract_class(self, handler):
        access = ObjectAccess(AccessType.INSTANTIATE)
        with pytest.raises(InstantiationError, match="Cannot instantiate abstract class"):
            handler.handle(AbstractClass, access)

    def test_non_abc_abstract_class(self, handler):
        """Test that we detect abstract classes even without ABC."""
        access = ObjectAccess(AccessType.INSTANTIATE)

        # Should raise for abstract class without ABC
        with pytest.raises(InstantiationError, match="Cannot instantiate abstract class"):
            handler.handle(NonABCAbstractClass, access)

        # Should raise for child class that doesn't implement abstract method
        with pytest.raises(InstantiationError, match="Cannot instantiate abstract class"):
            handler.handle(ChildWithoutImpl, access)

        # Should work for concrete implementation
        result = handler.handle(ConcreteImplementation, access)
        assert isinstance(result.value, ConcreteImplementation)
        assert result.value.abstract_method() == "implemented"

    def test_mixin_with_abstract_method(self, handler):
        """Test handling of mixin classes with abstract methods."""
        access = ObjectAccess(AccessType.INSTANTIATE)

        # Should detect abstract method in mixin
        with pytest.raises(InstantiationError, match="Cannot instantiate abstract class"):
            handler.handle(MixinWithAbstractMethod, access)

        # Create a class that uses the mixin but doesn't implement method
        class WithMixin(MixinWithAbstractMethod):
            pass

        with pytest.raises(InstantiationError, match="Cannot instantiate abstract class"):
            handler.handle(WithMixin, access)

        # Create a class that properly implements the abstract method
        class ProperImplementation(MixinWithAbstractMethod):
            def mixin_method(self):
                return "implemented"

        # Should work for proper implementation
        result = handler.handle(ProperImplementation, access)
        assert isinstance(result.value, ProperImplementation)
        assert result.value.mixin_method() == "implemented"

    def test_regular_concrete_class(self, handler):
        """Test that regular concrete classes work normally."""
        access = ObjectAccess(AccessType.INSTANTIATE)

        # Should work for regular concrete class
        result = handler.handle(ConcreteClass, access)
        assert isinstance(result.value, ConcreteClass)

    def test_security_check(self):
        handler = InstantiateHandler(STRICT_OBJECT_ACCESS_SECURITY)
        access = ObjectAccess(AccessType.INSTANTIATE)
        with pytest.raises(ObjectAccessSecurityError):
            handler.handle(TestClass, access)


class TestCallHandler:
    @pytest.fixture
    def handler(self):
        return CallHandler(ObjectAccessSecurityContext())

    def test_can_handle(self, handler):
        access = ObjectAccess(AccessType.CALL)
        assert handler.can_handle(lambda x: x, access)
        assert handler.can_handle(TestClass().method, access)
        assert not handler.can_handle(42, access)

    def test_successful_call(self, handler):
        func = lambda x: x * 2
        access = ObjectAccess(AccessType.CALL, args=(21,))
        result = handler.handle(func, access)
        assert result.value == 42
        assert result.metadata["args"] == (21,)

    def test_method_call(self, handler):
        obj = TestClass()
        access = ObjectAccess(AccessType.CALL, args=("test",))
        result = handler.handle(obj.method, access)
        assert result.value == "Method called with test"

    def test_invalid_arguments(self, handler):
        func = lambda x: x
        access = ObjectAccess(AccessType.CALL)  # Missing required argument
        with pytest.raises(CallError):
            handler.handle(func, access)

    def test_security_check(self):
        handler = CallHandler(STRICT_OBJECT_ACCESS_SECURITY)
        access = ObjectAccess(AccessType.CALL, args=(1,))
        with pytest.raises(ObjectAccessSecurityError):
            handler.handle(lambda x: x, access)


class TestAttributeHandler:
    @pytest.fixture
    def handler(self):
        return AttributeHandler(ObjectAccessSecurityContext())

    @pytest.fixture
    def test_obj(self):
        return TestClass("test_value")

    def test_can_handle(self, handler):
        assert handler.can_handle(None, ObjectAccess(AccessType.GET))
        assert handler.can_handle(None, ObjectAccess(AccessType.SET))
        assert not handler.can_handle(None, ObjectAccess(AccessType.CALL))

    def test_get_attribute(self, handler, test_obj):
        access = ObjectAccess(AccessType.GET, args=("value",))
        result = handler.handle(test_obj, access)
        assert result.value == "test_value"
        assert result.metadata["attribute"] == "value"

    def test_set_attribute(self, handler, test_obj):
        access = ObjectAccess(AccessType.SET, args=("value", "new_value"))
        handler.handle(test_obj, access)
        assert test_obj.value == "new_value"

    def test_nonexistent_attribute(self, handler, test_obj):
        access = ObjectAccess(AccessType.GET, args=("nonexistent",))
        with pytest.raises(AttributeError):
            handler.handle(test_obj, access)

    def test_security_check(self, test_obj):
        handler = AttributeHandler(STRICT_OBJECT_ACCESS_SECURITY)
        access = ObjectAccess(AccessType.SET, args=("value", "new_value"))
        with pytest.raises(ObjectAccessSecurityError):
            handler.handle(test_obj, access)
