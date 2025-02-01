import pytest
from pypaya_python_tools.importing.exceptions import ImportingError
from pypaya_python_tools.importing.manager import ImportManager
from pypaya_python_tools.importing.security import ImportSecurity


class TestImportManager:
    @pytest.fixture
    def security(self):
        return ImportSecurity(allow_file_imports=True)

    @pytest.fixture
    def manager(self, security):
        return ImportManager(security)

    def test_import_module(self, manager):
        # Test basic module import
        result = manager.import_module("json")
        assert result.__name__ == "json"

    def test_import_from_module(self, manager):
        # Test importing specific object from module
        result = manager.import_from_module("json", "loads")
        assert callable(result)

    def test_import_file(self, manager, tmp_path):
        # Test basic file import
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 42")

        result = manager.import_file(test_file)
        assert result.x == 42

    def test_import_from_file(self, manager, tmp_path):
        # Test importing specific object from file
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 42")

        result = manager.import_from_file(test_file, "x")
        assert result == 42

    def test_import_builtin(self, manager):
        # Test builtin import
        result = manager.import_builtin("len")
        assert result is len

    def test_security_integration(self, security, manager):
        # Test security settings are respected
        security.blocked_modules.add("os")
        with pytest.raises(ImportingError):
            manager.import_module("os")

    def test_nonexistent_source(self, manager):
        # Test handling of non-existent sources
        with pytest.raises(ImportingError):
            manager.import_module("nonexistent_module")
