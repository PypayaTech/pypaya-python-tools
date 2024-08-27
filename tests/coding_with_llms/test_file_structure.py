import pytest
import os
import tempfile
import shutil
from pypaya_python_tools.coding_with_llms.file_structure import get_directory_structure


@pytest.fixture
def temp_directory():
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Create a simple directory structure with some files
    os.makedirs(os.path.join(temp_dir, 'subdir1'))
    os.makedirs(os.path.join(temp_dir, 'subdir2'))

    with open(os.path.join(temp_dir, 'file1.txt'), 'w') as f:
        f.write('Content of file1')

    with open(os.path.join(temp_dir, 'subdir1', 'file2.txt'), 'w') as f:
        f.write('Content of file2')

    yield temp_dir

    # Cleanup after the test
    shutil.rmtree(temp_dir)


def test_get_directory_structure(temp_directory):
    expected_structure = """file1.txt
subdir1/
  file2.txt
subdir2/"""

    assert get_directory_structure(temp_directory) == expected_structure
