import pytest
from pypaya_python_tools.importing.import_manager import ImportManager
from pypaya_python_tools.importing.definitions import SourceType, ImportSource
from pypaya_python_tools.importing.security import ImportSecurityContext, STRICT_IMPORT_SECURITY
from pypaya_python_tools.importing.exceptions import ResolverError, ImportSecurityError
from pypaya_python_tools.importing.resolvers.base import ImportResolver, ResolveResult


class TestImportManager:
    @pytest.fixture
    def manager(self):
        return ImportManager()

    def test_import_module(self, manager):
        # Test importing whole module
        result = manager.import_object(ImportSource(SourceType.MODULE, "json"))
        assert result.__name__ == "json"

        # Test importing specific object
        result = manager.import_object(ImportSource(SourceType.MODULE, "json", name="loads"))
        assert callable(result)

    def test_import_builtin(self, manager):
        result = manager.import_object(ImportSource(SourceType.BUILTIN, name="len"))
        assert result is len

    def test_security_context(self):
        manager = ImportManager(STRICT_IMPORT_SECURITY)
        with pytest.raises(ImportSecurityError):
            manager.import_object(ImportSource(SourceType.FILE, "test.py"))

    def test_custom_resolver(self, manager):
        class CustomResolver(ImportResolver):
            def can_handle(self, source):
                return source.type == "CUSTOM"

            def resolve(self, source):
                return ResolveResult("custom_value")

        manager.register_resolver("CUSTOM", CustomResolver(ImportSecurityContext()))
        result = manager.import_object(ImportSource("CUSTOM", "dummy"))
        assert result == "custom_value"

    def test_error_handling(self, manager):
        # Test nonexistent module
        with pytest.raises(ResolverError):
            manager.import_object(ImportSource(SourceType.MODULE, "nonexistent_module"))

        # Test nonexistent resolver
        with pytest.raises(ResolverError):
            manager.import_object(ImportSource("UNKNOWN", "dummy"))
