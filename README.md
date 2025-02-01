# pypaya-python-tools

A comprehensive toolkit for Python developers to simplify common programming tasks and enable advanced Python features with a clean, intuitive API.

## Overview

`pypaya-python-tools` is a meta-package for Python developers that provides tools for:

- Dynamic importing of modules and objects
- Safe object access and manipulation
- Configuration-based object creation
- Plugin architecture development
- Dynamic code execution
- Working with coding LLMs

The package focuses on making advanced Python features safer, more consistent, and easier to use.

## Installation

```bash
pip install pypaya-python-tools
```

## Key Features

### Dynamic Imports

Import modules and objects dynamically with better error handling and security controls:

```python
from pypaya_python_tools.importing import import_module, import_object

# Import a module
json = import_module('json')

# Import a specific object from a module
dumps = import_object('json', 'dumps')

# Import from a file
MyClass = import_object('/path/to/file.py', 'MyClass')
```

### Object Operations

Access and manipulate object attributes and methods safely:

```python
from pypaya_python_tools.object_operations import get_attribute, set_attribute, call

# Safely get an attribute with a default value
value = get_attribute(obj, 'attr_name', default='default_value')

# Set an attribute with validation
set_attribute(obj, 'attr_name', new_value)

# Call a method safely
result = call(obj.method, arg1, arg2, keyword=value)
```

### Configuration-Based Objects

Create objects from configuration dictionaries:

```python
from pypaya_python_tools.create_from_config import create_instance

# Create an instance from configuration
config = {
    "module": "myapp.models",
    "class": "User",
    "kwargs": {
        "name": "Alice",
        "role": "admin"
    }
}

user = create_instance(config)
```

### Operation Chains

Chain operations together with context tracking and better error handling:

```python
from pypaya_python_tools.chains import ImportChain, OperationChain

# Import and use a class in one chain
user = (
    ImportChain()
    .from_module("myapp.models")
    .get_class("User")
    .to_access_chain()
    .instantiate(name="Bob")
    .get_attribute("profile")
    .value
)
```

### Code Execution

Execute Python code with better security and output capture:

```python
from pypaya_python_tools.execution import PythonREPL

# Create a REPL with security settings
repl = PythonREPL(security=ExecutionSecurity(allow_subprocess=False))

# Execute code and capture results
result = repl.execute("""
x = 5
y = 10
print(f"Sum: {x + y}")
""")

print(f"Output: {result.stdout}")
print(f"Result: {result.result}")
```

### LLM Code Tools

Present code to LLMs in optimal formats:

```python
from pypaya_python_tools.coding_with_llms import CodePresenter

# Create a presenter for a project
presenter = CodePresenter("/path/to/project")

# Show project structure
structure = presenter.show_structure()

# Show specific files
content = presenter.show_content(["main.py", "utils/helpers.py"])

# Combine structure and content
full_presentation = presenter.combine(content_paths=["main.py"])
```

## Subpackages

- `importing` - Tools for dynamic importing
- `object_operations` - Safe object attribute and method access
- `create_from_config` - Configuration-based object creation
- `chains` - Operation chaining with context tracking
- `execution` - Safe dynamic code execution
- `decorating` - Useful function and class decorators
- `coding_with_llms` - Tools for working with code in LLMs

## Example Use Cases

### Configuration-Driven Data Pipeline

```python
from pypaya_python_tools.create_from_config import create_instance

# Define pipeline stages from configuration
pipeline_config = [
    {
        "class": "DataValidator",
        "module": "myapp.pipeline",
        "kwargs": {
            "rules": ["no_empty", "no_duplicates"]
        }
    },
    {
        "class": "DataTransformer",
        "module": "myapp.pipeline",
        "kwargs": {
            "transformations": ["lowercase", "trim_whitespace"]
        }
    },
    {
        "class": "DataExporter",
        "module": "myapp.pipeline",
        "kwargs": {
            "format": "json",
            "destination": "output.json"
        }
    }
]

# Create the pipeline
pipeline = [create_instance(stage_config) for stage_config in pipeline_config]

# Process data through the pipeline
data = load_data()
for stage in pipeline:
    data = stage.process(data)
```

### Safe Runtime Object Manipulation

```python
from pypaya_python_tools.object_operations import (
    AccessManager, OperationSecurity, OperationType, Operation
)

# Create a security policy
security = OperationSecurity(
    allow_private_access=False,
    allow_protected_access=True,
    blocked_methods={"delete", "reset", "remove"}
)

# Create an access manager
manager = AccessManager(security)

# Safely access an object
def safe_access(user_obj, attr_name, operation_type, *args, **kwargs):
    """Safely access user objects with runtime validation."""
    operation = Operation(
        type=operation_type,
        args=args,
        kwargs=kwargs
    )
    
    try:
        return manager.access_object(user_obj, operation)
    except Exception as e:
        print(f"Access denied: {e}")
        return None

# Example usage
user_data = safe_access(
    user_object, 
    "profile", 
    OperationType.GET_ATTRIBUTE, 
    "profile"
)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
