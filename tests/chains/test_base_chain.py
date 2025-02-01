import pytest
from pypaya_python_tools.chains.base.chain import ObjectChain
from pypaya_python_tools.chains.base.context import ChainContext
from pypaya_python_tools.chains.base.state import ChainState
from pypaya_python_tools.chains.exceptions import ChainStateError


class TestChain(ObjectChain[int]):
    """Test implementation of ObjectChain"""
    def to_import_chain(self):
        pass
    def to_access_chain(self):
        pass
    def to_execution_chain(self):
        pass


def test_chain_initial_state():
    chain = TestChain()
    assert chain.state == ChainState.INITIAL


def test_chain_with_value():
    chain = TestChain(value=42)
    assert chain.state == ChainState.LOADED
    assert chain.value == 42


def test_chain_state_transition():
    chain = TestChain(value=42)
    assert chain.state == ChainState.LOADED
    _ = chain.value  # Access value
    assert chain.state == ChainState.COMPLETED


def test_chain_context():
    context = ChainContext()
    chain = TestChain(context=context)
    assert chain.context is context


def test_failed_chain():
    chain = TestChain()
    chain._state = ChainState.FAILED
    with pytest.raises(ChainStateError):
        _ = chain.value


def test_chain_context_manager():
    with TestChain(value=42) as chain:
        assert chain.value == 42


def test_chain_context_manager_with_error():
    with TestChain() as chain:
        chain._state = ChainState.FAILED
        with pytest.raises(ChainStateError):
            _ = chain.value
