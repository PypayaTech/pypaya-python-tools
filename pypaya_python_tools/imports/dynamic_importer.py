from typing import Any, Optional, Union, Dict, List, TypeVar
from types import ModuleType
from dataclasses import dataclass
import importlib
import importlib.util
import os
import sys
import logging
from contextlib import contextmanager
from pathlib import Path


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

    def __init__(self, config: ImportConfig = ImportConfig()):
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
        """Import a module using its fully qualified name.

        This method imports Python modules using the standard import mechanism.
        If base_path is provided, it will be temporarily added to sys.path.

        Args:
            module_name: Fully qualified module name (e.g., 'package.subpackage.module')
            base_path: Optional base directory to add to Python path

        Returns:
            The imported module

        Raises:
            ImportError: If module cannot be imported

        Examples:
            >>> importer = DynamicImporter()
            >>> math_module = importer.import_module('math')
            >>> custom_module = importer.import_module('mypackage.mymodule', base_path='/path/to/project')
        """
        if module_name in self._loaded_modules:
            self.logger.debug(f"Returning cached module {module_name}")
            return self._loaded_modules[module_name]

        try:
            if base_path:
                sys.path.insert(0, base_path)
                try:
                    module = importlib.import_module(module_name)
                finally:
                    sys.path.pop(0)
            else:
                module = importlib.import_module(module_name)

            self._loaded_modules[module_name] = module
            self.logger.debug(f"Successfully imported module {module_name}")
            return module

        except ImportError as e:
            self.logger.error(f"Failed to import module {module_name}: {str(e)}",
                              exc_info=self._config.debug)
            raise

    def import_object_from_module(self, import_path: str, base_path: Optional[str] = None) -> Any:
        """Import a specific object from a module using its fully qualified name.

        This method imports a specific object (class, function, variable, etc.)
        from a module using dot notation.

        Args:
            import_path: Fully qualified object path (e.g., 'package.module.Class')
            base_path: Optional base directory to add to Python path

        Returns:
            The imported object

        Raises:
            ImportError: If module cannot be imported
            AttributeError: If object doesn't exist in the module

        Examples:
            >>> importer = DynamicImporter()
            >>> sin_func = importer.import_object_from_module('math.sin')
            >>> MyClass = importer.import_object_from_module('mypackage.module.MyClass',
            ...                                             base_path='/path/to/project')
        """
        try:
            module_name, object_name = import_path.rsplit('.', 1)
            module = self.import_module(module_name, base_path)

            if not hasattr(module, object_name):
                raise AttributeError(
                    f"Module '{module_name}' has no attribute '{object_name}'"
                )

            obj = getattr(module, object_name)
            self.logger.debug(
                f"Successfully imported object {object_name} from module {module_name}"
            )
            return obj

        except (ImportError, AttributeError) as e:
            self.logger.error(f"Failed to import object {import_path}: {str(e)}",
                              exc_info=self._config.debug)
            raise

    def import_file(self, file_path: str, module_name: Optional[str] = None) -> ModuleType:
        """Import a module directly from a file path.

        This method imports a Python file as a module without requiring it to be
        in the Python path.

        Args:
            file_path: Path to the Python file
            module_name: Optional custom name for the module (defaults to file name)

        Returns:
            The imported module

        Raises:
            ImportError: If file cannot be imported
            FileNotFoundError: If file doesn't exist

        Examples:
            >>> importer = DynamicImporter()
            >>> module = importer.import_file('/path/to/my_module.py')
            >>> named_module = importer.import_file('local_module.py', module_name='custom_name')
        """
        try:
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"No file found at {file_path}")

            if not module_name:
                module_name = os.path.splitext(os.path.basename(file_path))[0]

            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Failed to create spec for {file_path}")

            module = importlib.util.module_from_spec(spec)
            self._loaded_modules[module_name] = module
            self._module_paths[module_name] = file_path

            if self._config.add_to_sys_modules:
                sys.modules[module_name] = module

            spec.loader.exec_module(module)
            self.logger.debug(f"Successfully imported file {file_path} as module {module_name}")
            return module

        except (ImportError, FileNotFoundError) as e:
            self.logger.error(f"Failed to import file {file_path}: {str(e)}",
                              exc_info=self._config.debug)
            raise

    def import_object_from_file(self, file_path: str, object_name: str) -> Any:
        """Import a specific object from a Python file.

        This method imports a specific object (class, function, variable, etc.)
        from a Python file.

        Args:
            file_path: Path to the Python file
            object_name: Name of the object to import

        Returns:
            The imported object

        Raises:
            ImportError: If file cannot be imported
            FileNotFoundError: If file doesn't exist
            AttributeError: If object doesn't exist in the file

        Examples:
            >>> importer = DynamicImporter()
            >>> MyClass = importer.import_object_from_file('/path/to/module.py', 'MyClass')
            >>> my_func = importer.import_object_from_file('local_module.py', 'my_function')
        """
        try:
            module = self.import_file(file_path)

            if not hasattr(module, object_name):
                raise AttributeError(
                    f"Module loaded from '{file_path}' has no attribute '{object_name}'"
                )

            obj = getattr(module, object_name)
            self.logger.debug(
                f"Successfully imported object {object_name} from file {file_path}"
            )
            return obj

        except (ImportError, FileNotFoundError, AttributeError) as e:
            self.logger.error(
                f"Failed to import object {object_name} from file {file_path}: {str(e)}",
                exc_info=self._config.debug
            )
            raise

    def safe_import(self, import_path: str, base_path: Optional[str] = None) -> Optional[Union[ModuleType, Any]]:
        """Safely attempt different import strategies for a given path.

        This method tries different import strategies in the following order:
            1. If the path points to an existing file, imports it as a file
            2. If the path contains dots and the last part is not a .py extension,
        treats it as an object import from a module
            3. Otherwise, treats it as a module import

        Args:
            import_path: Path, module name, or object path to import
            base_path: Optional base directory for imports

        Returns:
            Imported module/object if successful, None if all import attempts fail

        Examples:
            >>> importer = DynamicImporter()
            >>> # Try importing a file
            >>> module = importer.safe_import('/path/to/my_module.py')
            >>> # Try importing an object from module
            >>> obj = importer.safe_import('package.module.MyClass')
            >>> # Try importing a module
            >>> mod = importer.safe_import('package.module')
        """
        try:
            # First check if it's a file path
            if base_path:
                full_path = os.path.join(base_path, import_path)
            else:
                full_path = import_path

            if os.path.isfile(full_path) and full_path.endswith('.py'):
                self.logger.debug(f"Attempting file import for {full_path}")
                return self.import_file(full_path)

            # Then check if it's an object import (contains dots and last part isn't a .py extension)
            parts = import_path.split('.')
            if len(parts) > 1 and not parts[-1].endswith('.py'):
                self.logger.debug(f"Attempting object import for {import_path}")
                return self.import_object_from_module(import_path, base_path)

            # Finally, try module import
            self.logger.debug(f"Attempting module import for {import_path}")
            return self.import_module(import_path, base_path)

        except (ImportError, AttributeError, FileNotFoundError) as e:
            self.logger.warning(
                f"Safe import failed for {import_path}: {str(e)}",
                exc_info=self._config.debug
            )
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


def create_example_files(base_path: str) -> dict:
    """Create example files and return their paths for testing.

    Args:
        base_path: Base directory for creating example files

    Returns:
        Dictionary containing paths to created files
    """
    # Create directory structure
    examples_dir = os.path.join(base_path, 'examples')
    package_dir = os.path.join(examples_dir, 'mypackage')
    os.makedirs(package_dir, exist_ok=True)

    # Create __init__.py to make it a proper package
    with open(os.path.join(package_dir, '__init__.py'), 'w') as f:
        f.write('')

    # Create standalone module
    standalone_path = os.path.join(examples_dir, 'standalone.py')
    with open(standalone_path, 'w') as f:
        f.write('''
CONSTANT = "I'm a constant from standalone.py"

def standalone_function():
    return "I'm a function from standalone.py"

class StandaloneClass:
    def method(self):
        return "I'm a method from StandaloneClass"
''')

    # Create package module
    package_module_path = os.path.join(package_dir, 'module.py')
    with open(package_module_path, 'w') as f:
        f.write('''
from typing import Dict

class Configuration:
    def __init__(self, settings: Dict[str, str]):
        self.settings = settings

    def get_setting(self, key: str) -> str:
        return self.settings.get(key, "")

def create_config(settings: Dict[str, str]) -> Configuration:
    return Configuration(settings)
''')

    return {
        "standalone": standalone_path,
        "package_module": package_module_path,
        "base_dir": base_path
    }


def main():
    import tempfile

    # Create a temporary directory for our example files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create example files and get their paths
        paths = create_example_files(temp_dir)

        # Initialize importer with debug mode for better visibility
        config = ImportConfig(add_to_sys_modules=True, debug=True)
        importer = DynamicImporter(config)

        try:
            # 1. Demonstrate import_file
            print("\n1. Importing module from file:")
            standalone = importer.import_file(paths['standalone'])
            print(f"- Imported constant value: {standalone.CONSTANT}")
            print(f"- Called standalone function: {standalone.standalone_function()}")

            # 2. Demonstrate import_object_from_file
            print("\n2. Importing specific object from file:")
            StandaloneClass = importer.import_object_from_file(
                paths['standalone'],
                'StandaloneClass'
            )
            instance = StandaloneClass()
            print(f"- Called imported class method: {instance.method()}")

            # 3. Demonstrate import_module with package
            print("\n3. Importing module from package:")
            module = importer.import_module('examples.mypackage.module', base_path=temp_dir)
            config_obj = module.create_config({'test': 'value'})
            print(f"- Created configuration object: {config_obj.get_setting('test')}")

            # 4. Demonstrate import_object_from_module
            print("\n4. Importing specific object from module:")
            Configuration = importer.import_object_from_module(
                'examples.mypackage.module.Configuration',
                base_path=temp_dir
            )
            config_instance = Configuration({'demo': 'test'})
            print(f"- Used imported class: {config_instance.get_setting('demo')}")

            # 5. Demonstrate safe_import with different scenarios
            print("\n5. Testing safe_import with different inputs:")

            # Try file import
            result1 = importer.safe_import(paths['standalone'])
            print(f"- Safe import of file: {'Success' if result1 else 'Failed'}")

            # Try module import
            result2 = importer.safe_import('examples.mypackage.module', base_path=temp_dir)
            print(f"- Safe import of module: {'Success' if result2 else 'Failed'}")

            # Try non-existent import
            result3 = importer.safe_import('non_existent_module')
            print(f"- Safe import of non-existent module: {'Success' if result3 else 'Failed'}")

        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print("\nDemonstration completed.")


if __name__ == "__main__":
    main()
