import pytest
import os
import tempfile
import shutil
from pypaya_python_tools.coding_with_llms.file_structure import (
    get_directory_structure,
    generate_directory_structure,
    DirectoryStructureGenerator,
    OutputFormat
)


@pytest.fixture
def temp_directory():
    temp_dir = tempfile.mkdtemp()
    os.makedirs(os.path.join(temp_dir, 'subdir1'))
    os.makedirs(os.path.join(temp_dir, 'subdir2'))
    os.makedirs(os.path.join(temp_dir, 'empty_dir'))

    with open(os.path.join(temp_dir, 'file1.txt'), 'w') as f:
        f.write('Content of file1')

    with open(os.path.join(temp_dir, 'subdir1', 'file2.txt'), 'w') as f:
        f.write('Content of file2')

    with open(os.path.join(temp_dir, 'subdir1', 'script.py'), 'w') as f:
        f.write('print("Hello, World!")')

    with open(os.path.join(temp_dir, 'subdir2', 'data.csv'), 'w') as f:
        f.write('id,name\n1,John\n2,Jane')

    yield temp_dir
    shutil.rmtree(temp_dir)


def test_get_directory_structure(temp_directory):
    expected_structure = """empty_dir/
file1.txt
subdir1/
  file2.txt
  script.py
subdir2/
  data.csv"""
    assert get_directory_structure(temp_directory) == expected_structure


def test_generate_directory_structure_plain(temp_directory):
    expected_structure = """empty_dir/
file1.txt
subdir1/
  file2.txt
  script.py
subdir2/
  data.csv"""
    assert generate_directory_structure(temp_directory, OutputFormat.PLAIN) == expected_structure


def test_generate_directory_structure_tree(temp_directory):
    expected_structure = f"""{temp_directory}
├── empty_dir
├── file1.txt
├── subdir1
│   ├── file2.txt
│   └── script.py
└── subdir2
    └── data.csv"""
    assert generate_directory_structure(temp_directory, OutputFormat.TREE) == expected_structure


def test_generate_directory_structure_content(temp_directory):
    expected_content = """# Directory Structure

```
empty_dir/
file1.txt
subdir1/
  file2.txt
  script.py
subdir2/
  data.csv
```

# File Contents

## empty_dir/

### file1.txt
```
Content of file1
```

## subdir1/

### subdir1/file2.txt
```
Content of file2
```

### subdir1/script.py
```
print("Hello, World!")
```

## subdir2/

### subdir2/data.csv
```
id,name
1,John
2,Jane
```
"""
    assert generate_directory_structure(temp_directory, OutputFormat.CONTENT) == expected_content


def test_invalid_output_format(temp_directory):
    with pytest.raises(ValueError):
        generate_directory_structure(temp_directory, 'INVALID_FORMAT')


def test_include_extensions(temp_directory):
    expected_structure = """empty_dir/
file1.txt
subdir1/
  file2.txt
subdir2/"""
    assert generate_directory_structure(temp_directory, OutputFormat.PLAIN, include_extensions=['.txt']) == expected_structure


def test_exclude_extensions(temp_directory):
    expected_structure = """empty_dir/
subdir1/
  script.py
subdir2/
  data.csv"""
    assert generate_directory_structure(temp_directory, OutputFormat.PLAIN, exclude_extensions=['.txt']) == expected_structure


def test_include_and_exclude_extensions(temp_directory):
    expected_structure = """empty_dir/
subdir1/
  script.py
subdir2/"""
    assert generate_directory_structure(temp_directory, OutputFormat.PLAIN, include_extensions=['.py', '.txt'], exclude_extensions=['.txt']) == expected_structure


def test_tree_format_with_extensions(temp_directory):
    expected_structure = f"""{temp_directory}
├── empty_dir
├── subdir1
│   └── script.py
└── subdir2
    └── data.csv"""
    assert generate_directory_structure(temp_directory, OutputFormat.TREE, exclude_extensions=['.txt']) == expected_structure


def test_content_format_with_extensions(temp_directory):
    expected_content = """# Directory Structure

```
empty_dir/
subdir1/
  script.py
subdir2/
  data.csv
```

# File Contents

## empty_dir/

## subdir1/

### subdir1/script.py
```
print("Hello, World!")
```

## subdir2/

### subdir2/data.csv
```
id,name
1,John
2,Jane
```
"""
    assert generate_directory_structure(temp_directory, OutputFormat.CONTENT, exclude_extensions=['.txt']) == expected_content


def test_exclude_empty_directories(temp_directory):
    expected_structure = """file1.txt
subdir1/
  file2.txt
  script.py
subdir2/
  data.csv"""
    assert generate_directory_structure(temp_directory, OutputFormat.PLAIN, include_empty_directories=False) == expected_structure


def test_exclude_empty_directories_with_extensions(temp_directory):
    expected_structure = """subdir1/
  script.py"""
    assert generate_directory_structure(temp_directory, OutputFormat.PLAIN, include_extensions=['.py'], include_empty_directories=False) == expected_structure


def test_tree_format_exclude_empty_directories(temp_directory):
    expected_structure = f"""{temp_directory}
├── file1.txt
├── subdir1
│   ├── file2.txt
│   └── script.py
└── subdir2
    └── data.csv"""
    assert generate_directory_structure(temp_directory, OutputFormat.TREE, include_empty_directories=False) == expected_structure


def test_content_format_exclude_empty_directories(temp_directory):
    expected_content = """# Directory Structure

```
file1.txt
subdir1/
  file2.txt
  script.py
subdir2/
  data.csv
```

# File Contents

### file1.txt
```
Content of file1
```

## subdir1/

### subdir1/file2.txt
```
Content of file2
```

### subdir1/script.py
```
print("Hello, World!")
```

## subdir2/

### subdir2/data.csv
```
id,name
1,John
2,Jane
```
"""
    assert generate_directory_structure(temp_directory, OutputFormat.CONTENT, include_empty_directories=False) == expected_content
