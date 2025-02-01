import pytest
from pathlib import Path


@pytest.fixture
def temp_project(tmp_path):
    """
    Creates a temporary project structure for testing.
    """
    project_dir = tmp_path / "test_project"

    # Create directories
    (project_dir / "src" / "utils").mkdir(parents=True)
    (project_dir / "tests").mkdir()
    (project_dir / "docs").mkdir()
    (project_dir / ".git").mkdir()

    # Create files with content
    (project_dir / "src" / "main.py").write_text(
        "def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()"
    )
    (project_dir / "src" / "utils" / "helpers.py").write_text(
        "def helper():\n    return True"
    )
    (project_dir / "src" / "utils" / "config.py").write_text(
        "CONFIG = {'debug': True}"
    )
    (project_dir / "tests" / "test_main.py").write_text(
        "def test_main():\n    assert True"
    )
    (project_dir / "docs" / "README.md").write_text(
        "# Test Project\nThis is a test project."
    )
    (project_dir / ".git" / "config").write_text(
        "[core]\n    repositoryformatversion = 0"
    )

    return project_dir
