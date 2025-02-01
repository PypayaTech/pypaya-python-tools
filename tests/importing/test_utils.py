import pytest
from pypaya_python_tools.importing.exceptions import ImportingError
from pypaya_python_tools.importing.utils import (
    import_from_module,
    import_from_file,
    import_builtin,
    import_object
)
from pypaya_python_tools.importing.security import ImportSecurity


@pytest.fixture
def security():
    """Default security settings for testing."""
    return ImportSecurity(
        allow_file_imports=True  # Enable file imports for testing
    )


class TestBasicImports:
    """Test individual import utility functions."""

    def test_import_from_module(self):
        # Test object import (can't import whole module with import_from_module)
        loads = import_from_module("json", "loads")
        assert callable(loads)

        # Test nonexistent module
        with pytest.raises(ImportingError):
            import_from_module("nonexistent_module", "func")

        # Test nonexistent attribute
        with pytest.raises(ImportingError):
            import_from_module("json", "nonexistent")

    def test_import_from_file(self, tmp_path, security):
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def test_function():
    return "test"
TEST_CONSTANT = 42
""")

        # Test module import
        module = import_from_file(test_file, security=security)
        assert hasattr(module, "test_function")
        assert module.TEST_CONSTANT == 42

        # Test object import
        func = import_from_file(test_file, "test_function", security=security)
        assert func() == "test"

    def test_import_builtin(self):
        # Test existing builtin
        length_func = import_builtin("len")
        assert length_func is len

        # Test nonexistent builtin
        with pytest.raises(ImportingError):
            import_builtin("nonexistent")


class TestImportObject:
    """Test versatile import_object function."""

    def test_separate_path_name_format(self):
        """Test traditional module path + name format."""
        assert import_object("json", "dumps") == __import__("json").dumps
        assert import_object("json").__name__ == "json"

    def test_dict_format(self):
        """Test dictionary specification format."""
        # With name in dict
        obj = import_object({"path": "json", "name": "dumps"})
        assert obj == __import__("json").dumps

        # Without name in dict
        obj = import_object({"path": "json"}, "dumps")
        assert obj == __import__("json").dumps

    def test_file_imports(self, tmp_path, security):
        """Test file-based imports."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 42")

        # Different ways to import from file
        assert import_object(test_file, security=security).x == 42
        assert import_object(str(test_file), security=security).x == 42
        assert import_object({"path": str(test_file)}, security=security).x == 42

        # With specific attribute
        test_file.write_text("class Test: pass")
        assert import_object(test_file, "Test", security=security).__name__ == "Test"

    def test_security_integration(self):
        """Test security settings are respected."""
        security = ImportSecurity(allow_file_imports=False)

        # Should work (module import)
        import_object("json", security=security)

        # Should fail (file import)
        with pytest.raises(ImportingError):
            import_object("test.py", security=security)

    def test_error_handling(self, security):
        """Test various error conditions."""
        # Invalid dictionary
        with pytest.raises(ImportingError):
            import_object({"invalid": "format"}, security=security)

        # Nonexistent module
        with pytest.raises(ImportingError):
            import_object("nonexistent_module", "func", security=security)

        # Nonexistent attribute
        with pytest.raises(ImportingError):
            import_object("json", "nonexistent_function", security=security)

        # Invalid path
        with pytest.raises(ImportingError):
            import_object("/nonexistent/path.py", security=security)
