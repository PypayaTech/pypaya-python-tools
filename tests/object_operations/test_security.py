import pytest
from pypaya_python_tools.object_operations.security import OperationSecurity
from pypaya_python_tools.object_operations.exceptions import (
    SecurityError, AccessSecurityError, ModificationSecurityError
)


def test_security_defaults():
    security = OperationSecurity()
    assert security.enabled
    assert not security.allow_private_access
    assert not security.allow_protected_access
    assert not security.allow_modification
    assert not security.allow_dynamic_access


def test_private_access():
    security = OperationSecurity()
    with pytest.raises(AccessSecurityError):
        security.validate_access("__private")

    security.allow_private_access = True
    security.validate_access("__private")


def test_protected_access():
    security = OperationSecurity()
    with pytest.raises(AccessSecurityError):
        security.validate_access("_protected")

    security.allow_protected_access = True
    security.validate_access("_protected")


def test_allowed_methods():
    security = OperationSecurity(allowed_methods={"allowed_method"})
    security.validate_access("allowed_method", is_method=True)

    with pytest.raises(AccessSecurityError):
        security.validate_access("other_method", is_method=True)


def test_blocked_methods():
    security = OperationSecurity(blocked_methods={"blocked_method"})
    with pytest.raises(AccessSecurityError):
        security.validate_access("blocked_method", is_method=True)


def test_modification_validation():
    security = OperationSecurity()
    with pytest.raises(ModificationSecurityError):
        security.validate_modification("set_attribute")

    security.allow_modification = True
    security.validate_modification("set_attribute")


def test_container_modification():
    security = OperationSecurity(allow_modification=True)
    with pytest.raises(ModificationSecurityError):
        security.validate_modification("container_set")

    security.allow_container_modification = True
    security.validate_modification("container_set")


def test_security_disabled():
    security = OperationSecurity(enabled=False)
    security.validate_access("__private")
    security.validate_access("_protected")
    security.validate_modification("any_operation")
