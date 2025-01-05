import pytest
from pypaya_python_tools.importing.utils import (
    import_from_module,
    import_from_file,
    import_builtin
)
from pypaya_python_tools.importing.exceptions import ResolverError


def test_import_from_module():
    # Test importing module
    json = import_from_module("json")
    assert json.__name__ == "json"

    # Test importing object
    loads = import_from_module("json", "loads")
    assert callable(loads)


def test_import_from_file(tmp_path):
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("""
def test_function():
    return "test"
""")

    # Test importing file
    module = import_from_file(test_file)
    assert hasattr(module, "test_function")

    # Test importing object
    func = import_from_file(test_file, "test_function")
    assert func() == "test"


def test_import_builtin():
    length_func = import_builtin("len")
    assert length_func is len

    with pytest.raises(ResolverError):
        import_builtin("nonexistent")
