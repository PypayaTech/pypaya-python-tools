# pypaya-python-tools

A comprehensive Python toolkit that makes meta-programming, code manipulation, and dynamic execution both safe and elegant.

## Features by Package

### 1. Chains
Fluent interfaces for code manipulation and data flow
```python
from pypaya_python_tools.chains import ImportChain, NavigationChain

# Import, access and navigate in a single flow
result = (ImportChain()
          .from_module("myapp.models")
          .get_class("User")
          .to_access_chain()
          .instantiate(username="john")
          .to_navigation_chain()
          .navigate("profile.settings.theme")
          .value)
```

### 2. Decorators
Powerful function and class decorators
```python
from pypaya_python_tools.decorating import (
    singleton, synchronized, rate_limit, lazy_property,
    debug, retry, memoize
)

# Thread-safe singleton
@singleton
class Database:
    def __init__(self):
        self.connect()

# Rate limiting
@rate_limit(calls=100, period=60)  # 100 calls per minute
def api_request():
    pass

# Retry with exponential backoff
@retry(max_attempts=3, delay=1.0, backoff=2.0)
def unreliable_operation():
    pass

# Lazy property evaluation
class ExpensiveOperations:
    @lazy_property
    def complex_calculation(self):
        return sum(x * x for x in range(10000))

# Thread synchronization
@synchronized()
def thread_safe_operation():
    pass

# Debug information
@debug(log_args=True, log_result=True)
def tracked_function(x, y):
    return x + y
```

### 3. Object Access
Safe attribute access and method calls
```python
from pypaya_python_tools.object_access import safe_access, AccessManager

# Safe nested attribute access
value = safe_access(obj, "deeply.nested.attribute", default="fallback")

# Managed object access
manager = AccessManager(security_context=context)
result = manager.access_object(obj, {
    "type": "method",
    "name": "calculate",
    "args": [1, 2],
    "validate_result": True
})
```

### 4. Navigation 
Complex data structure traversal
```python
from pypaya_python_tools.navigation import Navigator

data = {
    "users": [
        {"name": "John", "settings": {"theme": "dark"}},
        {"name": "Alice", "settings": {"theme": "light"}}
    ]
}

nav = Navigator(data)

# Flexible navigation
themes = (nav.select("users")
            .filter(lambda u: u["name"] == "John")
            .map(lambda u: u["settings"]["theme"])
            .first())

# Pattern matching
results = nav.find_all("**.settings.theme")

# Value extraction
user_names = nav.extract("users[*].name")  # ["John", "Alice"]
```

### 5. Importing
Dynamic code importing and loading
```python
from pypaya_python_tools.importing import import_object, ImportManager

# Simple dynamic import
MyClass = import_object("myapp.models.MyClass")

# Managed imports with security
manager = ImportManager(security_context=context)
module = manager.from_file(
    path="/safe/path/module.py",
    validate_source=True
)

# Advanced importing
result = manager.import_from({
    "source": "file",
    "path": "/path/to/file.py",
    "class": "MyClass",
    "construct": True,
    "args": ["param1", "param2"]
})
```

### 6. Execution
Safe code execution control
```python
from pypaya_python_tools.execution import (
    ExecutionContext, CodeExecutor, REPL
)

# Secure execution environment
with ExecutionContext(
    max_time=5,    # 5 second timeout
    max_memory="100M",  # 100MB limit
    allowed_modules=["math", "json"]
) as ctx:
    result = ctx.run_code("""
        x = 10
        y = 20
        result = x * y
    """)
    print(ctx.get_variable("result"))  # 200

# Interactive REPL
repl = REPL(security_context=context)
repl.run("print('Hello from secure REPL')")

# Code executor
executor = CodeExecutor()
executor.with_globals({"x": 100})
executor.with_timeout(5)
result = executor.eval("x * 2")  # 200
```

### 7. Package Management
Unified package installation and management
```python
from pypaya_python_tools.package_management import (
    PackageManager, EnvironmentManager
)

# Simple package operations
pm = PackageManager()
pm.install("requests==2.26.0")
pm.update("pandas")
pm.uninstall("old-package")

# Environment management
with EnvironmentManager("my_env") as env:
    env.install_requirements("requirements.txt")
    env.execute("main.py")

# Conda support
conda = PackageManager(backend="conda")
conda.create_environment("ml-env")
conda.install("tensorflow")
```

### 8. Python Objects
Deep inspection and manipulation of Python objects
```python
from pypaya_python_tools.python_objects import (
    PythonClass, PythonCallable, ModuleInspector
)

# Class inspection
with PythonClass.from_path("myapp.models.User") as cls:
    print(f"Methods: {cls.get_methods()}")
    print(f"Properties: {cls.get_properties()}")
    print(f"Is abstract: {cls.is_abstract()}")
    
    # Validation and instantiation
    if not cls.is_abstract():
        instance = cls.instantiate(username="john")

# Function inspection
func = PythonCallable.from_object(my_function)
print(f"Parameters: {func.get_parameters()}")
print(f"Return type: {func.get_return_type()}")
print(f"Source:\n{func.get_source()}")

# Module inspection
inspector = ModuleInspector("myapp.models")
print(f"Classes: {inspector.get_classes()}")
print(f"Functions: {inspector.get_functions()}")
```
