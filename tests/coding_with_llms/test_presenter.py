import pytest
from pypaya_python_tools.coding_with_llms import CodePresenter, StructureFormat, ContentFormat
from pypaya_python_tools.coding_with_llms.exceptions import InvalidPathError, FileAccessError


class TestCodePresenter:
    """Tests for the CodePresenter class."""

    def test_initialization(self, temp_project):
        """Test if CodePresenter initializes correctly with a valid path."""
        presenter = CodePresenter(temp_project)
        assert presenter.root_path == temp_project

    def test_invalid_path(self):
        """Test if CodePresenter raises InvalidPathError for non-existent path."""
        with pytest.raises(InvalidPathError, match="Invalid project path"):
            CodePresenter("nonexistent/path")

    class TestStructureDisplay:
        """Tests for directory structure display functionality."""

        def test_plain_format(self, temp_project):
            """Test if plain format shows correct structure with proper indentation."""
            presenter = CodePresenter(temp_project)
            result = presenter.show_structure(
                format=StructureFormat.PLAIN
            )
            expected = """
docs/
  README.md
src/
  utils/
    config.py
    helpers.py
  main.py
tests/
  test_main.py""".lstrip()

            assert result.strip() == expected

        def test_tree_format(self, temp_project):
            """Test if tree format shows correct structure with proper tree characters."""
            presenter = CodePresenter(temp_project)
            result = presenter.show_structure(
                format=StructureFormat.TREE
            )
            expected = """
test_project
├── docs/
│   └── README.md
├── src/
│   ├── utils/
│   │   ├── config.py
│   │   └── helpers.py
│   └── main.py
└── tests/
    └── test_main.py""".lstrip()

            assert result.strip() == expected

        def test_markdown_format(self, temp_project):
            """Test if Markdown format shows correct structure within code blocks."""
            presenter = CodePresenter(temp_project)
            result = presenter.show_structure(
                format=StructureFormat.MARKDOWN
            )
            expected = """
# Project Structure
```
docs/
  README.md
src/
  utils/
    config.py
    helpers.py
  main.py
tests/
  test_main.py
```""".lstrip()

            assert result.strip() == expected

        def test_max_depth(self, temp_project):
            """Test if max_depth parameter correctly limits directory traversal."""
            presenter = CodePresenter(temp_project)
            result = presenter.show_structure(
                format=StructureFormat.PLAIN,
                max_depth=1
            )
            expected = """
docs/
src/
tests/""".lstrip()

            assert result.strip() == expected

        def test_extension_filter(self, temp_project):
            """Test if extension filtering shows only specified file types."""
            presenter = CodePresenter(temp_project)
            result = presenter.show_structure(
                format=StructureFormat.PLAIN,
                include_extensions=[".py"]
            )
            expected = """
src/
  utils/
    config.py
    helpers.py
  main.py
tests/
  test_main.py""".lstrip()

            assert result.strip() == expected

    class TestContentDisplay:
        """Tests for file content display functionality."""

        def test_single_file_content_markdown(self, temp_project):
            """Test if markdown format shows file content with proper formatting."""
            presenter = CodePresenter(temp_project)
            result = presenter.show_content(["src/main.py"])
            expected = """
## src/main.py
```python
def main():
    print('Hello, World!')

if __name__ == '__main__':
    main()
```""".lstrip()

            assert result.strip() == expected

        def test_multiple_files_content(self, temp_project):
            """Test if multiple file contents are displayed correctly."""
            presenter = CodePresenter(temp_project)
            result = presenter.show_content(
                ["src/main.py", "src/utils/helpers.py"]
            )
            expected = """
## src/main.py
```python
def main():
    print('Hello, World!')

if __name__ == '__main__':
    main()
```

## src/utils/helpers.py
```python
def helper():
    return True
```""".lstrip()

            assert result.strip() == expected

        def test_plain_format(self, temp_project):
            """Test if plain format shows file content without markdown formatting."""
            presenter = CodePresenter(temp_project)
            result = presenter.show_content(
                ["src/main.py"],
                format=ContentFormat.PLAIN
            )

            # Check plain text formatting
            assert "--- src/main.py ---" in result
            assert "def main():" in result
            assert "```" not in result  # Should not contain markdown

        def test_invalid_file(self, temp_project):
            """Test if showing content of non-existent file raises error."""
            presenter = CodePresenter(temp_project)
            with pytest.raises(InvalidPathError, match=f"Invalid path: nonexistent.py"):
                presenter.show_content(["nonexistent.py"])

        def test_content_with_exclude_patterns(self, temp_project):
            """Test if exclude patterns work correctly for content display."""
            presenter = CodePresenter(temp_project)
            result = presenter.show_content(
                ["src"],
                recursive=True,
                exclude_patterns=["helpers.py"]
            )

            assert "helpers.py" not in result
            assert "main.py" in result
            assert "config.py" in result

        def test_content_with_extensions_and_patterns(self, temp_project):
            """Test if both extension and pattern filtering work together."""
            presenter = CodePresenter(temp_project)
            result = presenter.show_content(
                ["src", "docs"],
                recursive=True,
                include_extensions=[".py"],
                exclude_patterns=["helpers.py"]
            )

            assert "helpers.py" not in result
            assert "README.md" not in result
            assert "main.py" in result
            assert "config.py" in result

    class TestCombinedOutput:
        """Tests for combined structure and content display."""

        def test_structure_and_content(self, temp_project):
            """Test if structure and content are combined correctly."""
            presenter = CodePresenter(temp_project)
            result = presenter.combine(
                content_paths=["src/main.py"],
                structure_header="# Files",
                content_header="# Contents"
            )
            expected = """
# Files

docs/
  README.md
src/
  utils/
    config.py
    helpers.py
  main.py
tests/
  test_main.py

# Contents

## src/main.py
```python
def main():
    print('Hello, World!')

if __name__ == '__main__':
    main()
```""".lstrip()

            assert result.strip() == expected

        def test_structure_only(self, temp_project):
            """Test if combine works correctly without content paths."""
            presenter = CodePresenter(temp_project)
            result = presenter.combine()
            expected = """
# Project Structure

docs/
  README.md
src/
  utils/
    config.py
    helpers.py
  main.py
tests/
  test_main.py""".lstrip()

            assert result.strip() == expected

        def test_custom_separator(self, temp_project):
            """Test if custom separator is used correctly in combined output."""
            presenter = CodePresenter(temp_project)
            result = presenter.combine(
                content_paths=["src/main.py"],
                separator="\n---\n"
            )
            expected = """
# Project Structure

docs/
  README.md
src/
  utils/
    config.py
    helpers.py
  main.py
tests/
  test_main.py

---

# File Contents

## src/main.py
```python
def main():
    print('Hello, World!')

if __name__ == '__main__':
    main()
```""".lstrip()

            assert result.strip() == expected

        def test_combined_with_filters(self, temp_project):
            """Test if all filters work correctly in combined output."""
            presenter = CodePresenter(temp_project)
            result = presenter.combine(
                content_paths=["src"],
                recursive=True,
                include_extensions=[".py"],
                exclude_patterns=["helpers.py"],
                max_depth=2
            )

            # Check structure part
            assert "src/" in result
            assert "utils/" in result
            assert "helpers.py" not in result
            assert "README.md" not in result

            # Check content part
            content_section = result.split("# File Contents")[1]
            assert "main.py" in content_section
            assert "config.py" in content_section
            assert "helpers.py" not in content_section

        def test_combined_max_depth_only(self, temp_project):
            """Test if max_depth works correctly in combined output."""
            presenter = CodePresenter(temp_project)
            result = presenter.combine(
                content_paths=["src"],
                max_depth=1
            )

            structure_section = result.split("# File Contents")[0]
            assert "src/" in structure_section
            assert "utils/" not in structure_section

            # Content should still show all files as max_depth only affects structure
            content_section = result.split("# File Contents")[1]
            assert "main.py" in content_section

    class TestEdgeCases:
        """Tests for edge cases and special situations."""

        def test_empty_directory(self, tmp_path):
            """Test handling of empty directories."""
            empty_dir = tmp_path / "empty"
            empty_dir.mkdir()
            presenter = CodePresenter(empty_dir)
            result = presenter.show_structure(format=StructureFormat.TREE)
            expected = "empty"
            assert result.strip() == expected

        def test_binary_file_handling(self, temp_project):
            """Test handling of binary files."""
            binary_file = temp_project / "binary.dat"
            binary_file.write_bytes(b'\x00\x01\x02\x03')
            presenter = CodePresenter(temp_project)
            result = presenter.show_content(["binary.dat"])
            expected = """
## binary.dat
[Binary file]""".lstrip()

            assert result.strip() == expected

        def test_very_deep_nesting(self, tmp_path):
            """Test handling of deeply nested directory structures."""
            # Create a controlled depth of 3 levels
            deep = tmp_path / "deep"
            deep.mkdir()
            current = deep
            for i in range(3):
                current = current / f"level_{i}"
                current.mkdir()

            presenter = CodePresenter(deep)
            result = presenter.show_structure(format=StructureFormat.TREE)
            expected = """
deep
└── level_0/
    └── level_1/
        └── level_2""".lstrip()

            assert result.strip() == expected

    class TestInputValidation:
        """Tests for input validation."""

        def test_invalid_max_depth(self, temp_project):
            """Test if negative max_depth raises ValueError."""
            presenter = CodePresenter(temp_project)
            with pytest.raises(ValueError):
                presenter.show_structure(max_depth=-1)

        def test_empty_paths_list(self, temp_project):
            """Test if empty paths list raises ValueError."""
            presenter = CodePresenter(temp_project)
            with pytest.raises(ValueError):
                presenter.show_content([])

        def test_none_paths_list(self, temp_project):
            """Test if None paths list raises ValueError."""
            presenter = CodePresenter(temp_project)
            with pytest.raises(ValueError):
                presenter.show_content(None)
