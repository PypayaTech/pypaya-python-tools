import pytest
import os
import sys
from pypaya_python_tools.imports.dynamic_importer import DynamicImporter, ImportConfig


@pytest.fixture
def importer():
    config = ImportConfig(add_to_sys_modules=True, debug=True)
    return DynamicImporter(config)


@pytest.fixture
def temp_module(tmp_path):
    module_path = tmp_path / "temp_module.py"
    module_content = """
def test_function():
    return "Hello from test_function"

class TestClass:
    @staticmethod
    def test_method():
        return "Hello from TestClass.test_method"
    """
    module_path.write_text(module_content)
    return str(module_path)


def test_import_module(importer):
    os_module = importer.import_module('os')
    assert os_module == os


def test_import_object(importer):
    path_join = importer.import_object('os.path.join')
    assert callable(path_join)
    assert path_join('a', 'b') == os.path.join('a', 'b')


def test_import_file(importer, temp_module):
    module = importer.import_file(temp_module)
    assert hasattr(module, 'test_function')
    assert module.test_function() == "Hello from test_function"


def test_import_object_from_file(importer, temp_module):
    test_function = importer.import_object_from_file(temp_module, 'test_function')
    assert callable(test_function)
    assert test_function() == "Hello from test_function"


def test_safe_import(importer):
    assert importer.safe_import('non_existent_module') is None
    assert isinstance(importer.safe_import('os'), type(os))


def test_load_plugins(importer, tmp_path):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "plugin1.py").write_text("class Plugin1: pass")
    (plugin_dir / "plugin2.py").write_text("class Plugin2: pass")
    plugins = importer.load_plugins(str(plugin_dir))
    assert len(plugins) == 2
    assert all(isinstance(p, type) for p in plugins)


def test_reload_module(importer, temp_module):
    module = importer.import_file(temp_module)
    importer.reload_module(module.__name__)
    reloaded_module = sys.modules[module.__name__]
    assert reloaded_module is not module


def test_add_to_path(tmp_path):
    new_path = str(tmp_path)
    DynamicImporter.add_to_path(new_path)
    assert new_path in sys.path


def test_temporary_path(importer, tmp_path):
    new_path = str(tmp_path)
    assert new_path not in sys.path
    with importer.temporary_path(new_path):
        assert new_path in sys.path
    assert new_path not in sys.path


def test_get_imported_modules(importer):
    importer.import_module('os')
    imported_modules = importer.get_imported_modules()
    assert 'os' in imported_modules


def test_import_from_base_path(importer, tmp_path):
    (tmp_path / "custom_module.py").write_text("""
def custom_function():
    return "Hello from custom_function"
    """)

    module = importer.import_module('custom_module', base_path=str(tmp_path))
    assert hasattr(module, 'custom_function')
    assert module.custom_function() == "Hello from custom_function"


def test_import_package(importer, tmp_path):
    package_dir = tmp_path / "custom_package"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("")
    (package_dir / "submodule.py").write_text("""
def submodule_function():
    return "Hello from submodule_function"
    """)

    module = importer.import_module('custom_package.submodule', base_path=str(tmp_path))
    assert hasattr(module, 'submodule_function')
    assert module.submodule_function() == "Hello from submodule_function"


if __name__ == "__main__":
    pytest.main()
