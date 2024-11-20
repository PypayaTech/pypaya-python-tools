from typing import Any, Dict, List, Union
import logging
import inspect
import copy
from pypaya_python_tools.imports.dynamic_importer import DynamicImporter, ImportConfig


class ClassInstanceFactory:
    """Creates class instances from string-based module and class configurations."""

    def __init__(self,
                 dynamic_importer: DynamicImporter = None):
        """
        Initialize the ClassInstanceFactory.

        Args:
            dynamic_importer (DynamicImporter): An instance of DynamicImporter for flexible importing.
        """
        self.importer = dynamic_importer or DynamicImporter(ImportConfig())
        self.logger = logging.getLogger(__name__)

    def create(self, config: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Any, List[Any]]:
        """
        Create one or multiple objects based on the provided configuration.

        Args:
            config (Union[Dict[str, Any], List[Dict[str, Any]]]): Configuration for object(s) creation.
                Can be either a single configuration dictionary or a list of configuration dictionaries.
                For a single instance, the dictionary must include:
                - 'module': str - the module path (e.g., 'datetime')
                - 'class': str (optional) - the class name (e.g., 'datetime')
                And may include:
                - 'args': list - positional arguments for the class constructor
                - 'kwargs': dict - keyword arguments for the class constructor

        Returns:
            Union[Any, List[Any]]: The created object(s).

        Raises:
            ValueError: If the configuration is invalid.
            ImportError: If a module cannot be imported.
            TypeError: If the arguments don't match the class constructor.
        """
        if isinstance(config, list):
            return [self.create(item) for item in config]

        if not isinstance(config, dict):
            return config

        config_copy = copy.deepcopy(config)

        # Validate args and kwargs if present
        if "args" in config_copy and not isinstance(config_copy["args"], list):
            raise ValueError("'args' must be a list")
        if "kwargs" in config_copy and not isinstance(config_copy["kwargs"], dict):
            raise ValueError("'kwargs' must be a dictionary")

        # Validate class name if present
        if "class" in config_copy and not isinstance(config_copy["class"], str):
            raise ValueError("'class' must be a string")

        # Handle the case where the entire config is a valid object
        if "module" not in config_copy and "class" not in config_copy:
            return config_copy

        if "module" not in config_copy:
            raise ValueError("Configuration must include a 'module' key")

        module_name = config_copy.pop("module")
        class_name = config_copy.pop("class", None)
        args = config_copy.pop("args", [])
        kwargs = config_copy.pop("kwargs", {})

        try:
            module = self.importer.import_module(module_name)

            if class_name:
                class_obj = self.importer.import_object_from_module(f"{module_name}.{class_name}")
            else:
                class_obj = module

            if inspect.isclass(class_obj) and inspect.isabstract(class_obj):
                raise ValueError(f"Cannot instantiate abstract class: {class_obj.__name__}")

            # Recursively create nested objects in args
            args = [self.create(arg) if isinstance(arg, dict) else arg for arg in args]

            # Recursively create nested objects in kwargs
            for key, value in kwargs.items():
                if isinstance(value, dict):
                    kwargs[key] = self.create(value)
                elif isinstance(value, list):
                    kwargs[key] = [self.create(item) if isinstance(item, dict) else item for item in value]

            return class_obj(*args, **kwargs)
        except ImportError:
            self.logger.error(f"Error importing module {module_name}")
            raise
        except Exception as e:
            self.logger.error(f"Error creating object from {module_name}: {str(e)}")
            raise


def main():
    # Initialize the DynamicImporter and ConfigurableObjectGenerator
    importer = DynamicImporter(ImportConfig())
    generator = ClassInstanceFactory(importer)

    # Example 1: Create a datetime object
    date_config = {
        "module": "datetime",
        "class": "datetime",
        "args": [2023, 6, 15],
        "kwargs": {"hour": 10, "minute": 30}
    }
    date_obj = generator.create(date_config)
    print("Example 1 - Datetime object:")
    print(f"Created date: {date_obj}")
    print(f"Type: {type(date_obj)}")
    print()

    # Example 2: Create a namedtuple
    namedtuple_config = {
        "module": "collections",
        "class": "namedtuple",
        "args": ["Person", "name age"],
    }
    Person = generator.create(namedtuple_config)
    john = Person("John", 30)
    print("Example 2 - Namedtuple:")
    print(f"Created namedtuple: {john}")
    print(f"Type: {type(john)}")
    print()

    # Example 3: Nested configuration
    nested_config = {
        "module": "collections",
        "class": "namedtuple",
        "args": ["Employee", "name position start_date"],
        "kwargs": {
            "defaults": [None, {
                "module": "datetime",
                "class": "date",
                "args": [2023, 6, 15]
            }]
        }
    }
    Employee = generator.create(nested_config)
    alice = Employee("Alice", "Developer")
    print("Example 3 - Nested configuration:")
    print(f"Created employee: {alice}")
    print(f"Type: {type(alice)}")

    # Example 4: Using package.subpackage.module (urllib.parse)
    urlparse_config = {
        "module": "urllib.parse",
        "class": "urlparse",
        "args": ["https://www.example.com/path?key=value"]
    }
    parsed_url = generator.create(urlparse_config)
    print("Example 4 - Using urllib.parse.urlparse:")
    print(f"Parsed URL: {parsed_url}")
    print(f"Scheme: {parsed_url.scheme}")
    print(f"Netloc: {parsed_url.netloc}")
    print(f"Path: {parsed_url.path}")
    print(f"Query: {parsed_url.query}")
    print(f"Type: {type(parsed_url)}")


if __name__ == "__main__":
    main()
