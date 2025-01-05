import builtins
import pytest
from pathlib import Path
from pypaya_python_tools.importing.definitions import SourceType, ImportSource
from pypaya_python_tools.importing.security import SecurityContext, STRICT_SECURITY, SecurityError
from pypaya_python_tools.importing.resolvers.base import ResolveResult
from pypaya_python_tools.importing.resolvers.module import ModuleResolver
from pypaya_python_tools.importing.resolvers.file import FileResolver
from pypaya_python_tools.importing.resolvers.builtin import BuiltinResolver
from pypaya_python_tools.importing.exceptions import ResolverError


class TestModuleResolver:
    @pytest.fixture
    def resolver(self):
        return ModuleResolver(SecurityContext())

    def test_can_handle(self, resolver):
        assert resolver.can_handle(ImportSource(SourceType.MODULE, "json"))
        assert not resolver.can_handle(ImportSource(SourceType.FILE, "test.py"))

    def test_resolve_module(self, resolver):
        source = ImportSource(SourceType.MODULE, "json")
        result = resolver.resolve(source)
        assert result.value.__name__ == "json"
        assert isinstance(result, ResolveResult)

    def test_resolve_object_from_module(self, resolver):
        source = ImportSource(SourceType.MODULE, "json", name="loads")
        result = resolver.resolve(source)
        assert callable(result.value)
        assert result.metadata["module"].__name__ == "json"

    def test_resolve_nonexistent_module(self, resolver):
        with pytest.raises(ResolverError):
            resolver.resolve(ImportSource(SourceType.MODULE, "nonexistent_module"))

    def test_resolve_nonexistent_attribute(self, resolver):
        with pytest.raises(ResolverError):
            resolver.resolve(ImportSource(SourceType.MODULE, "json", name="nonexistent"))


class TestFileResolver:
    @pytest.fixture
    def resolver(self):
        return FileResolver(SecurityContext())

    @pytest.fixture
    def test_file(self, tmp_path):
        file_path = tmp_path / "test_module.py"
        file_path.write_text("""
def test_function():
    return "test"

TEST_CONSTANT = "constant"
""")
        return file_path

    def test_can_handle(self, resolver):
        assert resolver.can_handle(ImportSource(SourceType.FILE, "test.py"))
        assert not resolver.can_handle(ImportSource(SourceType.MODULE, "json"))

    def test_resolve_file(self, resolver, test_file):
        source = ImportSource(SourceType.FILE, test_file)
        result = resolver.resolve(source)

        # Check basic attributes
        assert result is not None
        assert result.metadata is not None
        assert isinstance(result.metadata, dict)

        # Check metadata
        assert "file_path" in result.metadata
        assert "module" in result.metadata
        assert "module_name" in result.metadata
        assert result.metadata["file_path"] == test_file
        assert result.metadata["module"].__name__ == test_file.stem
        assert result.metadata["module_name"] == test_file.stem

        # Check value
        assert hasattr(result.value, "test_function")
        assert hasattr(result.value, "TEST_CONSTANT")

        # Verify functionality
        assert result.value.test_function() == "test"
        assert result.value.TEST_CONSTANT == "constant"

    def test_resolve_object_from_file(self, resolver, test_file):
        source = ImportSource(SourceType.FILE, test_file, name="test_function")
        result = resolver.resolve(source)
        assert callable(result.value)
        assert result.value() == "test"

    def test_resolve_constant_from_file(self, resolver, test_file):
        source = ImportSource(SourceType.FILE, test_file, name="TEST_CONSTANT")
        result = resolver.resolve(source)
        assert result.value == "constant"

    def test_security_checks(self):
        resolver = FileResolver(STRICT_SECURITY)
        with pytest.raises(SecurityError):
            resolver.resolve(ImportSource(SourceType.FILE, "test.py"))

    def test_trusted_paths(self, tmp_path):
        security = SecurityContext(trusted_paths=[tmp_path])
        resolver = FileResolver(security)

        safe_file = tmp_path / "safe.py"
        safe_file.write_text("x = 1")

        unsafe_file = Path("unsafe.py")

        # Safe path should work
        resolver.resolve(ImportSource(SourceType.FILE, safe_file))

        # Unsafe path should fail
        with pytest.raises(SecurityError):
            resolver.resolve(ImportSource(SourceType.FILE, unsafe_file))


class TestBuiltinResolver:
    @pytest.fixture
    def resolver(self):
        return BuiltinResolver(SecurityContext())

    def test_can_handle(self, resolver):
        # Valid builtin source
        assert resolver.can_handle(ImportSource(SourceType.BUILTIN, name="len"))

        # Non-builtin sources
        assert not resolver.can_handle(ImportSource(SourceType.MODULE, "json"))
        assert not resolver.can_handle(ImportSource(SourceType.FILE, "test.py"))

    def test_resolve_builtin(self, resolver):
        source = ImportSource(SourceType.BUILTIN, name="len")
        result = resolver.resolve(source)

        # Check value
        assert result.value is len

        # Check metadata
        assert result.metadata is not None
        assert result.metadata["builtin"] is True
        assert result.metadata["name"] == "len"
        assert result.metadata["module"] is builtins

        # Test functionality
        assert result.value([1, 2, 3]) == 3

    def test_resolve_nonexistent_builtin(self, resolver):
        with pytest.raises(ResolverError):
            resolver.resolve(ImportSource(SourceType.BUILTIN, name="nonexistent"))

    def test_builtin_source_validation(self):
        # Must specify name
        with pytest.raises(ValueError, match="name must be specified"):
            ImportSource(SourceType.BUILTIN)

        # Location should not be specified
        with pytest.raises(ValueError, match="location should not be specified"):
            ImportSource(SourceType.BUILTIN, location="builtins", name="len")

        # Valid builtin source
        source = ImportSource(SourceType.BUILTIN, name="len")
        assert source.type == SourceType.BUILTIN
        assert source.name == "len"
        assert source.location is None
