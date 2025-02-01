import pytest
from pypaya_python_tools.chains.object_operation import OperationChain
from pypaya_python_tools.chains.base.state import ChainState
from pypaya_python_tools.object_operations.exceptions import OperationError
from pypaya_python_tools.object_operations.security import OperationSecurity


class TestClass:
    def __init__(self):
        self.public_value = 42
        self._protected_value = 43
        self.__private_value = 44

    def public_method(self):
        return self.public_value

    def _protected_method(self):
        return self._protected_value

    def __private_method(self):
        return self.__private_value


@pytest.fixture
def test_object():
    return TestClass()


@pytest.fixture
def permissive_security():
    """Security config that allows all operations"""
    return OperationSecurity(
        allow_private_access=True,
        allow_protected_access=True,
        allow_modification=True,
        allow_dynamic_access=True
    )


@pytest.fixture
def restricted_security():
    """Security config that restricts most operations"""
    return OperationSecurity(
        allow_private_access=False,
        allow_protected_access=False,
        allow_modification=False,
        allow_dynamic_access=False
    )


@pytest.fixture
def permissive_chain(test_object, permissive_security):
    return OperationChain(value=test_object, security=permissive_security)


@pytest.fixture
def restricted_chain(test_object, restricted_security):
    return OperationChain(value=test_object, security=restricted_security)


def test_get_public_attribute(restricted_chain):
    result = restricted_chain.get_attribute("public_value")
    assert result.value == 42


def test_get_protected_attribute_denied(restricted_chain):
    with pytest.raises(OperationError) as exc_info:
        restricted_chain.get_attribute("_protected_value")
    assert "Protected member access denied" in str(exc_info.value)


def test_get_private_attribute_denied(restricted_chain):
    with pytest.raises(OperationError) as exc_info:
        restricted_chain.get_attribute("__private_value")
    assert "Private member access denied" in str(exc_info.value)


def test_set_attribute_denied(restricted_chain):
    with pytest.raises(OperationError) as exc_info:
        restricted_chain.set_attribute("public_value", 100)
    assert "set_attribute failed: Attribute modification is not allowed" in str(exc_info.value)


def test_configure_denied(restricted_chain):
    with pytest.raises(OperationError) as exc_info:
        restricted_chain.configure({"public_value": 200})
    assert "configure failed: set_attribute failed: Attribute modification is not allowed" in str(exc_info.value)


def test_call_public_method(permissive_chain):
    chain = permissive_chain.get_attribute("public_method")
    result = chain.call()
    assert result.value == 42


def test_call_protected_method_denied(restricted_chain):
    with pytest.raises(OperationError) as exc_info:
        restricted_chain.get_attribute("_protected_method")
    assert "Protected member access denied" in str(exc_info.value)


def test_call_private_method_denied(restricted_chain):
    with pytest.raises(OperationError) as exc_info:
        restricted_chain.get_attribute("__private_method")
    assert "Private member access denied" in str(exc_info.value)


# Permissive security tests
def test_get_protected_attribute_allowed(permissive_chain):
    result = permissive_chain.get_attribute("_protected_value")
    assert result.value == 43


def test_get_private_attribute_allowed(permissive_chain):
    result = permissive_chain.get_attribute("_TestClass__private_value")  # Use mangled name
    assert result.value == 44


def test_set_attribute_allowed(permissive_chain):
    permissive_chain.set_attribute("public_value", 100)
    assert permissive_chain.get_attribute("public_value").value == 100


def test_configure_allowed(permissive_chain):
    permissive_chain.configure({"public_value": 200})
    assert permissive_chain.get_attribute("public_value").value == 200


def test_call_protected_method_allowed(permissive_chain):
    chain = permissive_chain.get_attribute("_protected_method")
    result = chain.call()
    assert result.value == 43


def test_call_private_method_allowed(permissive_chain):
    chain = permissive_chain.get_attribute("_TestClass__private_method")  # Use mangled name
    result = chain.call()
    assert result.value == 44


# Edge cases and error handling
def test_nonexistent_attribute(restricted_chain):
    with pytest.raises(OperationError):
        restricted_chain.get_attribute("nonexistent")


def test_chain_state_transitions(restricted_chain):
    assert restricted_chain.state == ChainState.LOADED
    result = restricted_chain.get_attribute("public_value")
    assert result.state == ChainState.MODIFIED
    _ = result.value
    assert result.state == ChainState.COMPLETED


def test_chain_conversion(restricted_chain):
    # First get a valid value to convert
    result = restricted_chain.get_attribute("public_value")

    import_chain = result.to_import_chain()
    assert import_chain.value == result.value

    exec_chain = result.to_execution_chain()
    assert exec_chain.value == result.value
