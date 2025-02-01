import pytest
from pypaya_python_tools.chains.importing import ImportChain
from pypaya_python_tools.chains.base.state import ChainState
from pypaya_python_tools.importing import ImportingError


def test_import_module():
    chain = ImportChain()
    result = chain.from_module("json")
    assert result.state == ChainState.LOADED
    assert result.value.__name__ == "json"


def test_import_from_module():
    chain = ImportChain()
    result = chain.from_module("json", "dumps")
    assert result.state == ChainState.LOADED
    assert callable(result.value)


def test_import_builtin():
    chain = ImportChain()
    result = chain.get_builtin("len")
    assert result.state == ChainState.LOADED
    assert result.value is len


def test_invalid_module():
    chain = ImportChain()
    with pytest.raises(ImportingError):
        chain.from_module("nonexistent_module")


def test_invalid_object():
    chain = ImportChain()
    chain.from_module("json")
    with pytest.raises(ImportingError):
        chain.get_object("nonexistent_object")


def test_get_class():
    chain = ImportChain()
    chain.from_module("json").get_class("JSONDecoder")
    assert chain.state == ChainState.MODIFIED


def test_chain_conversion():
    chain = ImportChain()
    chain.from_module("json")

    access_chain = chain.to_access_chain()
    assert access_chain.value == chain.value

    exec_chain = chain.to_execution_chain()
    assert exec_chain.value == chain.value
