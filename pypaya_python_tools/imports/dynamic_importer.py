from typing import Any, Optional, Union, Dict, List, TypeVar
from dataclasses import dataclass
import importlib
import importlib.util
import os
import sys
import logging
import tempfile
from types import ModuleType
from contextlib import contextmanager


T = TypeVar('T')


@dataclass
class ImportConfig:
    """Configuration for DynamicImporter.

    Args:
        debug: Enable debug logging.
        add_to_sys_modules: Add imported modules to sys.modules.
    """
    debug: bool = False
    add_to_sys_modules: bool = True


class DynamicImporter:
    """A flexible dynamic import utility.

    This class provides methods to dynamically import modules, objects, and files.

    Args:
        config: ImportConfig object with importer settings.
    """

    def __init__(self, config: ImportConfig):
        self._config = config
        self._loaded_modules: Dict[str, ModuleType] = {}
        self._module_paths: Dict[str, str] = {}
        self._setup_logging()

    def _setup_logging(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG if self._config.debug else logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def import_module(self, module_name: str, base_path: Optional[str] = None) -> ModuleType:
        """Import a module.

        Args:
            module_name: Name of the module to import.
            base_path (Optional[str]): Base path for relative imports.

        Returns:
            The imported module.

        Raises:
            SecurityError: If the import is not allowed.
            ImportError: If the module cannot be imported.
        """
        if module_name in self._loaded_modules:
            return self._loaded_modules[module_name]
        try:
            if base_path:
                file_path = os.path.join(base_path, *module_name.split('.')) + '.py'
                if os.path.isfile(file_path):
                    return self.import_file(file_path, base_path)
            sys.path.insert(0, base_path)
            try:
                module = importlib.import_module(module_name)
            finally:
                sys.path.pop(0)

            self._loaded_modules[module_name] = module
            return module
        except ImportError as e:
            self.logger.error(f"Failed to import module {module_name}: {str(e)}", exc_info=self._config.debug)
            raise

    def import_object(self, import_path: str, base_path: Optional[str] = None) -> Any:
        """Import an object from a module.

        Args:
            import_path: Dot-separated path to the object.
            base_path (Optional[str]): Base path for relative imports.

        Returns:
            The imported object.

        Raises:
            SecurityError: If the import is not allowed.
            ImportError: If the object cannot be imported.
            AttributeError: If the object is not found in the module.
        """
        module_name, object_name = import_path.rsplit('.', 1)
        module = self.import_module(module_name, base_path)
        return getattr(module, object_name)

    def import_file(self, file_path: str, base_path: Optional[str] = None) -> ModuleType:
        """Import a module from a file.

        Args:
            file_path: Path to the file to import.
            base_path (Optional[str]): Base path for relative imports.

        Returns:
            The imported module.

        Raises:
            SecurityError: If the import is not allowed.
            ImportError: If the file cannot be imported.
        """
        full_path = os.path.join(base_path, file_path) if base_path else file_path
        module_name = os.path.splitext(os.path.basename(full_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, full_path)
        if spec is None:
            raise ImportError(f"Failed to create spec for {full_path}")
        module = importlib.util.module_from_spec(spec)
        self._loaded_modules[module_name] = module
        self._module_paths[module_name] = full_path
        if self._config.add_to_sys_modules:
            sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def import_object_from_file(self, file_path: str, object_name: str, base_path: Optional[str] = None) -> Any:
        """Import an object from a file.

        Args:
            file_path: Path to the file containing the object.
            object_name: Name of the object to import.
            base_path (Optional[str]): Base path for relative imports.

        Returns:
            The imported object.

        Raises:
            SecurityError: If the import is not allowed.
            ImportError: If the file cannot be imported.
            AttributeError: If the object is not found in the module.
        """
        module = self.import_file(file_path, base_path)
        return getattr(module, object_name)

    def safe_import(self, import_path: str, base_path: Optional[str] = None) -> Optional[Union[ModuleType, Any]]:
        """Safely import a module, object, or file.

        Args:
            import_path: Path to the module, object, or file to import.
            base_path (Optional[str]): Base path for relative imports.

        Returns:
            The imported module, object, or None if import fails.
        """
        try:
            full_path = os.path.join(base_path, import_path) if base_path else import_path
            if os.path.isfile(full_path):
                return self.import_file(import_path, base_path)
            elif '.' in import_path:
                return self.import_object(import_path, base_path)
            else:
                return self.import_module(import_path, base_path)
        except (ImportError, AttributeError):
            self.logger.warning(f"Safe import failed for {import_path}", exc_info=self._config.debug)
            return None

    def load_plugins(self, plugin_dir: str, base_class: Optional[type] = None) -> List[Any]:
        """Load plugins from a directory.

        Args:
            plugin_dir: Directory containing plugin files.
            base_class: Optional base class for filtering plugins.

        Returns:
            List of loaded plugin classes.
        """
        plugins = []
        for filename in os.listdir(plugin_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    module = self.import_file(os.path.join(plugin_dir, filename))
                    for attribute_name in dir(module):
                        attribute = getattr(module, attribute_name)
                        if isinstance(attribute, type):
                            if base_class is None or issubclass(attribute, base_class):
                                plugins.append(attribute)
                                self.logger.info(f"Loaded plugin {attribute.__name__} from {filename}")
                except (ImportError) as e:
                    self.logger.error(f"Error loading plugin {filename}: {str(e)}", exc_info=self._debug)
        return plugins

    def reload_module(self, module_name: str) -> None:
        """
        Reload a previously imported module.

        Args:
            module_name (str): The name of the module to reload.

        Raises:
            ImportError: If the module has not been previously imported by this DynamicImporter.
        """
        if module_name not in self._loaded_modules:
            raise ImportError(f"Module {module_name} has not been imported by this DynamicImporter")
        if module_name in self._module_paths:
            self.import_file(self._module_paths[module_name])
        else:
            self._loaded_modules[module_name] = importlib.reload(self._loaded_modules[module_name])
        self.logger.info(f"Successfully reloaded module {module_name}")

    @staticmethod
    def add_to_path(directory: str) -> None:
        """
        Add a directory to the Python path.

        Args:
            directory (str): Directory to add to the Python path.
        """
        abs_path = os.path.abspath(directory)
        if abs_path not in sys.path:
            sys.path.append(abs_path)
            logging.info(f"Added {abs_path} to Python path")

    @contextmanager
    def temporary_path(self, directory: str):
        """Temporarily add a directory to the Python path.

        Args:
            directory: Directory to temporarily add to the Python path.

        Yields:
            None
        """
        abs_path = os.path.abspath(directory)
        sys.path.append(abs_path)
        try:
            yield
        finally:
            sys.path.remove(abs_path)

    def get_imported_modules(self) -> Dict[str, ModuleType]:
        """Get all modules imported by this DynamicImporter.

        Returns:
            Dictionary of module names to module objects.
        """
        return self._loaded_modules.copy()


def create_example_files(base_path):
    """Create example files for demonstration."""
    os.makedirs(os.path.join(base_path, 'examples', 'plugins'), exist_ok=True)
    os.makedirs(os.path.join(base_path, 'examples', 'sample_package'), exist_ok=True)

    # Create sample_module.py
    with open(os.path.join(base_path, 'examples', 'sample_module.py'), 'w') as f:
        f.write('''
def sample_function():
    return "This is a sample function from sample_module.py"

class SampleClass:
    def method(self):
        return "This is a sample method of the SampleClass from sample_module.py"
''')

    # Create sample_package/sample_submodule.py
    with open(os.path.join(base_path, 'examples', 'sample_package', 'sample_submodule.py'), 'w') as f:
        f.write('''
def submodule_function():
    return "This is a function from sample_submodule.py"
''')

    # Create plugins
    for i in range(1, 3):
        with open(os.path.join(base_path, 'examples', 'plugins', f'plugin{i}.py'), 'w') as f:
            f.write(f'''
class Plugin{i}:
    def run(self):
        return f"Running Plugin{i}"
''')


def main():
    # Create a temporary directory for our example files
    with tempfile.TemporaryDirectory() as temp_dir:
        create_example_files(temp_dir)

        config = ImportConfig(
            add_to_sys_modules=True,
            debug=True
        )
        importer = DynamicImporter(config)

        print("1. Importing a module:")
        sample_module = importer.import_module('examples.sample_module', base_path=temp_dir)
        print(f"Imported sample_module: {sample_module}")
        print(f"Result of sample_function: {sample_module.sample_function()}")

        print("\n2. Importing an object:")
        SampleClass = importer.import_object('examples.sample_module.SampleClass', base_path=temp_dir)
        sample_instance = SampleClass()
        print(f"Result of SampleClass.method: {sample_instance.method()}")

        print("\n3. Importing from a package:")
        submodule_function = importer.import_object('examples.sample_package.sample_submodule.submodule_function',
                                                    base_path=temp_dir)
        print(f"Result of submodule_function: {submodule_function()}")

        print("\n4. Loading plugins:")
        plugins_dir = os.path.join(temp_dir, 'examples', 'plugins')
        plugins = importer.load_plugins(plugins_dir)
        for plugin_class in plugins:
            plugin = plugin_class()
            print(f"Result of {plugin_class.__name__}.run: {plugin.run()}")

        print("\n5. Safe import:")
        safe_import_result = importer.safe_import('non_existent_module', base_path=temp_dir)
        print(f"Safe import result of non-existent module: {safe_import_result}")

        print("\nDynamicImporter demonstration completed.")


if __name__ == "__main__":
    main()
