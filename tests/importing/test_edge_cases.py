import pytest
from pypaya_python_tools.importing.import_manager import ImportManager
from pypaya_python_tools.importing.definitions import SourceType, ImportSource
from pypaya_python_tools.importing.exceptions import ResolverError


class TestEdgeCases:
    @pytest.fixture
    def manager(self):
        return ImportManager()

    def test_circular_imports(self, manager, tmp_path):
        # Create files with circular imports
        file1 = tmp_path / "module1.py"
        file2 = tmp_path / "module2.py"

        file1.write_text("from module2 import func2\ndef func1(): return func2()")
        file2.write_text("from module1 import func1\ndef func2(): return func1()")

        with pytest.raises(ResolverError):
            manager.import_object(ImportSource(SourceType.FILE, file1))

    def test_malformed_python_file(self, manager, tmp_path):
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("this is not valid python!!!")

        with pytest.raises(ResolverError):
            manager.import_object(ImportSource(SourceType.FILE, bad_file))

    def test_empty_file(self, manager, tmp_path):
        empty_file = tmp_path / "empty.py"
        empty_file.touch()

        # Should work but return empty module
        result = manager.import_object(ImportSource(SourceType.FILE, empty_file))
        assert not any(name for name in dir(result)
                       if not name.startswith('__'))

    def test_unicode_handling(self, manager, tmp_path):
        unicode_file = tmp_path / "unicode.py"
        unicode_file.write_text('TEST = "测试"')

        result = manager.import_object(ImportSource(SourceType.FILE, unicode_file, name="TEST"))
        assert result == "测试"

    def test_memory_leaks(self, manager):
        import sys
        import gc

        initial_modules = set(sys.modules.keys())

        # Import and delete many times
        for _ in range(100):
            manager.import_object(ImportSource(SourceType.MODULE, "json"))
            gc.collect()

        # Check if modules were properly cleaned up
        final_modules = set(sys.modules.keys())
        assert len(final_modules - initial_modules) <= 1  # Allow for json module
