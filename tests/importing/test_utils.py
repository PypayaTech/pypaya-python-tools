import pytest
from pypaya_python_tools.importing.utils import (
    import_from_module,
    import_from_file,
    import_builtin,
    import_object
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


def test_import_object_separate_format():
    """Test the original module path + name format still works."""
    obj = import_object("json", "dumps")
    assert obj == __import__("json").dumps


def test_import_object_dict_format():
    """Test the new dictionary format."""
    obj = import_object({"path": "json", "name": "dumps"})
    assert obj == __import__("json").dumps


def test_import_object_dict_format_without_name():
    """Test dictionary format falls back to name parameter."""
    obj = import_object({"path": "json"}, "dumps")
    assert obj == __import__("json").dumps


def test_import_object_full_dotted_path():
    """Test the full dotted path format."""
    obj = import_object("json.dumps")
    assert obj == __import__("json").dumps


def test_import_object_invalid_dict():
    """Test error handling for invalid dictionary format."""
    with pytest.raises(ValueError):
        import_object({"invalid": "format"})


def test_import_object_invalid_module():
    """Test error handling for invalid module."""
    with pytest.raises(ResolverError):
        import_object("nonexistent_module", "func")


def test_import_object_invalid_name():
    """Test error handling for invalid object name."""
    with pytest.raises(ResolverError):
        import_object("json", "nonexistent_function")
