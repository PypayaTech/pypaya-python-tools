import pytest
from pathlib import Path
from pypaya_python_tools.importing import ImportingSecurityError
from pypaya_python_tools.importing.source import ImportSource, SourceType
from pypaya_python_tools.importing.security import ImportSecurity
from pypaya_python_tools.importing.exceptions import ResolverError, ImportingError
from pypaya_python_tools.importing.resolvers.base import ResolveResult
from pypaya_python_tools.importing.resolvers.module import ModuleResolver
from pypaya_python_tools.importing.resolvers.file import FileResolver


class TestModuleResolver:
    @pytest.fixture
    def security(self):
        return ImportSecurity()

    @pytest.fixture
    def resolver(self, security):
        return ModuleResolver(security)

    def test_can_handle(self, resolver):
        assert resolver.can_handle(ImportSource(type=SourceType.MODULE, location="json"))
        assert not resolver.can_handle(ImportSource(type=SourceType.FILE, location="test.py"))

    def test_resolve_module(self, resolver):
        result = resolver.resolve(ImportSource(
            type=SourceType.MODULE,
            location="json"
        ))
        assert isinstance(result, ResolveResult)
        assert result.value.__name__ == "json"
        assert result.metadata["type"] == "module"

    def test_resolve_object_from_module(self, resolver):
        result = resolver.resolve(ImportSource(
            type=SourceType.MODULE,
            location="json",
            name="loads"
        ))
        assert callable(result.value)
        assert result.metadata["type"] == "module_attribute"
        assert result.metadata["module"] == "json"
        assert result.metadata["name"] == "loads"

    def test_security_blocked_module(self, security, resolver):
        security.blocked_modules.add("os")
        with pytest.raises(ImportingSecurityError):
            resolver.resolve(ImportSource(
                type=SourceType.MODULE,
                location="os"
            ))

    def test_security_trusted_modules(self, security, resolver):
        security.trusted_modules = {"json"}
        # Should work
        resolver.resolve(ImportSource(
            type=SourceType.MODULE,
            location="json"
        ))
        # Should fail
        with pytest.raises(ImportingSecurityError):
            resolver.resolve(ImportSource(
                type=SourceType.MODULE,
                location="os"
            ))

    def test_nonexistent_module(self, resolver):
        with pytest.raises(ResolverError):
            resolver.resolve(ImportSource(
                type=SourceType.MODULE,
                location="nonexistent_module"
            ))

    def test_nonexistent_attribute(self, resolver):
        with pytest.raises(ResolverError):
            resolver.resolve(ImportSource(
                type=SourceType.MODULE,
                location="json",
                name="nonexistent"
            ))


class TestFileResolver:
    @pytest.fixture
    def security(self):
        return ImportSecurity(allow_file_imports=True)

    @pytest.fixture
    def resolver(self, security):
        return FileResolver(security)

    @pytest.fixture
    def test_file(self, tmp_path):
        file_path = tmp_path / "test_module.py"
        file_path.write_text("""
def test_function():
    return "test"

TEST_CONSTANT = "constant"

class TestClass:
    def method(self):
        return "method"
""")
        return file_path

    def test_can_handle(self, resolver):
        # Basic type checking
        assert resolver.can_handle(ImportSource(type=SourceType.FILE, location="test.py"))
        assert not resolver.can_handle(ImportSource(type=SourceType.MODULE, location="json"))

    def test_resolve_file_module(self, resolver, test_file):
        # Test importing entire module from file
        result = resolver.resolve(ImportSource(
            type=SourceType.FILE,
            location=test_file
        ))
        assert isinstance(result, ResolveResult)
        assert result.metadata["type"] == "file_module"
        assert hasattr(result.value, "test_function")
        assert result.value.TEST_CONSTANT == "constant"

    def test_resolve_function(self, resolver, test_file):
        # Test importing specific function
        result = resolver.resolve(ImportSource(
            type=SourceType.FILE,
            location=test_file,
            name="test_function"
        ))
        assert callable(result.value)
        assert result.value() == "test"

    def test_resolve_class(self, resolver, test_file):
        # Test importing class
        result = resolver.resolve(ImportSource(
            type=SourceType.FILE,
            location=test_file,
            name="TestClass"
        ))
        instance = result.value()
        assert instance.method() == "method"

    def test_security_file_imports_disabled(self, security, resolver):
        # Test when file imports are disabled
        security.allow_file_imports = False
        with pytest.raises(ImportingSecurityError):
            resolver.resolve(ImportSource(
                type=SourceType.FILE,
                location="any.py"
            ))

    def test_security_trusted_paths(self, security, resolver, tmp_path):
        # Test trusted paths functionality
        security.trusted_paths = {tmp_path}

        # Safe file in trusted path
        safe_file = tmp_path / "safe.py"
        safe_file.write_text("x = 1")

        # Unsafe file outside trusted paths
        unsafe_file = Path("unsafe.py")

        # Should work
        resolver.resolve(ImportSource(type=SourceType.FILE, location=safe_file))

        # Should fail
        with pytest.raises(ImportingSecurityError):
            resolver.resolve(ImportSource(type=SourceType.FILE, location=unsafe_file))

    def test_malformed_file(self, resolver, tmp_path):
        # Test handling of invalid Python files
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("this is not valid python!!!")

        with pytest.raises(ResolverError):
            resolver.resolve(ImportSource(type=SourceType.FILE, location=bad_file))
