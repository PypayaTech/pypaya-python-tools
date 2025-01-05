import pytest
from pypaya_python_tools.importing.security import SecurityContext, STRICT_SECURITY, SecurityError
from pypaya_python_tools.object_access.definitions import AccessType, ObjectAccess
from pypaya_python_tools.object_access.access_manager import AccessManager
from pypaya_python_tools.object_access.exceptions import InstantiationError


class TestAccessManager:
    @pytest.fixture
    def manager(self):
        return AccessManager()

    def test_instantiate_access(self, manager):
        class TestClass:
            def __init__(self, value):
                self.value = value

        access = ObjectAccess(
            AccessType.INSTANTIATE,
            args=("test",)
        )
        result = manager.access_object(TestClass, access)
        assert isinstance(result, TestClass)
        assert result.value == "test"

    def test_call_access(self, manager):
        def test_func(x):
            return x * 2

        access = ObjectAccess(
            AccessType.CALL,
            args=(21,)
        )
        result = manager.access_object(test_func, access)
        assert result == 42

    def test_attribute_access(self, manager):
        class TestClass:
            def __init__(self):
                self.value = "test"

        obj = TestClass()

        # Get attribute
        get_access = ObjectAccess(
            AccessType.GET,
            args=("value",)
        )
        result = manager.access_object(obj, get_access)
        assert result == "test"

        # Set attribute
        set_access = ObjectAccess(
            AccessType.SET,
            args=("value", "new_test")
        )
        manager.access_object(obj, set_access)
        assert obj.value == "new_test"

    def test_security_restrictions(self):
        manager = AccessManager(STRICT_SECURITY)

        class TestClass:
            pass

        # Test instantiation restriction
        with pytest.raises(SecurityError):
            manager.access_object(
                TestClass,
                ObjectAccess(AccessType.INSTANTIATE)
            )

        # Test modification restriction
        obj = TestClass()
        with pytest.raises(SecurityError):
            manager.access_object(
                obj,
                ObjectAccess(AccessType.SET, args=("value", 42))
            )

    def test_custom_handler(self, manager):
        from pypaya_python_tools.object_access.handlers.base import AccessHandler, AccessResult

        class CustomHandler(AccessHandler):
            def can_handle(self, obj, access):
                return access.type == "CUSTOM"

            def handle(self, obj, access):
                return AccessResult("custom_result")

        manager.register_handler("CUSTOM", CustomHandler(SecurityContext()))
        result = manager.access_object(None, ObjectAccess("CUSTOM"))
        assert result == "custom_result"
