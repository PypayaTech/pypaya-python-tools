from pathlib import Path
from typing import List, Optional, Union
from pypaya_python_tools.coding_with_llms.formats import StructureFormat, ContentFormat
from pypaya_python_tools.coding_with_llms.exceptions import InvalidPathError, FileAccessError


class CodePresenter:
    def __init__(self, path: str):
        """Initialize CodePresenter with project path."""
        self.root_path = Path(path).resolve()  # resolve to get absolute path
        if not self.root_path.exists() or not self.root_path.is_dir():
            raise InvalidPathError(f"Invalid project path: {path}")

    def show_structure(
            self,
            format: StructureFormat = StructureFormat.TREE,
            include_extensions: Optional[List[str]] = None,
            exclude_patterns: Optional[List[str]] = None,
            max_depth: Optional[int] = None,
            include_empty_dirs: bool = False
    ) -> str:
        """Generate directory structure representation."""
        if max_depth is not None and max_depth < 0:
            raise ValueError("max_depth must be non-negative")

        content = self._generate_structure(
            self.root_path,
            include_extensions,
            exclude_patterns,
            max_depth,
            include_empty_dirs,
            is_root=True
        )

        if format == StructureFormat.PLAIN:
            return content
        elif format == StructureFormat.TREE:
            return f"{self.root_path.name}\n{self._convert_to_tree(content)}"
        else:  # MARKDOWN
            return f"# Project Structure\n```\n{content}\n```"

    def show_content(
            self,
            paths: Union[str, List[str]],
            format: ContentFormat = ContentFormat.MARKDOWN,
            recursive: bool = False,
            include_extensions: Optional[List[str]] = None,
            exclude_patterns: Optional[List[str]] = None
    ) -> str:
        """
        Show content of specified files or all files in specified directories.

        Args:
            paths: Single path or list of paths to files or directories
            format: Output format (MARKDOWN or PLAIN)
            recursive: If True, include files in subdirectories
            include_extensions: Optional list of file extensions to include
            exclude_patterns: Optional list of patterns to exclude
        """
        if paths is None or (isinstance(paths, list) and not paths):
            raise ValueError("Paths list cannot be empty")

        if isinstance(paths, str):
            paths = [paths]

        result = []
        for path in paths:
            file_path = self.root_path / path
            if not file_path.exists():
                raise InvalidPathError(f"Invalid path: {path}")

            if file_path.is_file():
                if not self._should_exclude(file_path, exclude_patterns):
                    if not include_extensions or any(file_path.name.endswith(ext) for ext in include_extensions):
                        result.append(self._format_file_content(path, file_path, format))
            elif file_path.is_dir():
                files = self._get_directory_files(file_path, recursive, include_extensions, exclude_patterns)
                for file in sorted(files):
                    rel_path = str(file.relative_to(self.root_path))
                    result.append(self._format_file_content(rel_path, file, format))

        return "\n\n".join(result)

    def combine(
            self,
            content_paths: Optional[Union[str, List[str]]] = None,
            structure_header: str = "# Project Structure",
            content_header: str = "# File Contents",
            separator: str = "\n\n",
            recursive: bool = False,
            include_extensions: Optional[List[str]] = None,
            exclude_patterns: Optional[List[str]] = None,
            max_depth: Optional[int] = None
    ) -> str:
        """
        Combine structure and content display.

        Args have been expanded to include all filtering options from both show_structure and show_content.
        """
        structure = self.show_structure(
            format=StructureFormat.PLAIN,
            include_extensions=include_extensions,
            exclude_patterns=exclude_patterns,
            max_depth=max_depth
        )
        base = f"{structure_header}\n\n{structure}"

        if content_paths:
            content = self.show_content(
                paths=content_paths,
                recursive=recursive,
                include_extensions=include_extensions,
                exclude_patterns=exclude_patterns
            )
            if separator == "\n\n":
                return f"{base}\n\n{content_header}\n\n{content}"
            else:
                return f"{base}\n{separator}\n{content_header}\n\n{content}"

        return base

    def _should_exclude(self, path: Path, exclude_patterns: Optional[List[str]]) -> bool:
        """Check if path should be excluded based on patterns."""
        # Always exclude hidden files/directories by default
        if path.name.startswith('.'):
            return True

        if not exclude_patterns:
            return False

        rel_path = str(path.relative_to(self.root_path))
        for pattern in exclude_patterns:
            if Path(rel_path).match(pattern) or Path(rel_path).match("*/" + pattern):
                return True
        return False

    def _generate_structure(
            self,
            path: Path,
            include_extensions: Optional[List[str]],
            exclude_patterns: Optional[List[str]],
            max_depth: Optional[int],
            include_empty_dirs: bool,
            current_depth: int = 0,
            prefix: str = "",
            is_root: bool = False
    ) -> str:
        """Recursively generate directory structure."""
        if max_depth is not None and current_depth > max_depth:
            return ""

        result = []
        try:
            # Get all items and filter excluded ones first
            items = [
                item for item in sorted(path.iterdir())
                if not self._should_exclude(item, exclude_patterns)
            ]
        except PermissionError:
            return ""

        # Process directories first, then files
        dirs = []
        files = []

        for item in items:
            if item.is_dir():
                if max_depth is None or current_depth < max_depth:
                    # If filtering by extension, check if directory contains matching files
                    if include_extensions:
                        has_matching_files = any(
                            f.name.endswith(tuple(include_extensions))
                            for f in item.rglob("*")
                            if f.is_file() and not self._should_exclude(f, exclude_patterns)
                        )
                        if has_matching_files:
                            dirs.append(item)
                    else:
                        dirs.append(item)
            elif item.is_file():
                if max_depth is None or current_depth < max_depth:
                    if not include_extensions or any(item.name.endswith(ext) for ext in include_extensions):
                        files.append(item)

        # Add directories
        for item in dirs:
            # Add trailing slash only if it's not a leaf directory or has contents
            has_contents = any(i for i in item.iterdir() if not self._should_exclude(i, exclude_patterns))
            name = f"{item.name}{'/' if has_contents else ''}"
            if is_root:
                result.append(name)
            else:
                result.append(f"{prefix}{name}")

            if max_depth is None or current_depth < max_depth:
                sub_content = self._generate_structure(
                    item,
                    include_extensions,
                    exclude_patterns,
                    max_depth,
                    include_empty_dirs,
                    current_depth + 1,
                    "  " if is_root else prefix + "  ",
                    False
                )
                if sub_content:
                    result.append(sub_content)

        # Add files
        for item in files:
            if is_root:
                result.append(item.name)
            else:
                result.append(f"{prefix}{item.name}")

        return "\n".join(filter(None, result))

    def _convert_to_tree(self, plain_structure: str) -> str:
        """Convert plain structure to tree format."""
        if not plain_structure:
            return ""

        lines = plain_structure.split('\n')
        result = []
        levels = []  # Track items at each level

        # Process each line
        for i, line in enumerate(lines):
            if not line:
                continue

            # Calculate current level based on indentation
            indent = len(line) - len(line.lstrip())
            level = indent // 2
            content = line.lstrip()

            # Adjust levels list
            while len(levels) > level:
                levels.pop()
            while len(levels) < level:
                levels.append(False)

            # Determine if this is the last item at this level
            is_last = True
            for next_line in lines[i + 1:]:
                next_indent = len(next_line) - len(next_line.lstrip())
                next_level = next_indent // 2
                if next_level == level:
                    is_last = False
                    break
                if next_level < level:
                    break

            # Update levels
            if len(levels) == level:
                levels.append(is_last)
            else:
                levels[level] = is_last

            # Build the prefix
            prefix = ""
            for j in range(level):
                prefix += "    " if levels[j] else "│   "
            prefix += "└── " if is_last else "├── "

            # Special case for root level items
            if level == 0:
                prefix = "└── " if is_last else "├── "

            result.append(prefix + content)

        return "\n".join(result)

    def _get_directory_files(
            self,
            dir_path: Path,
            recursive: bool,
            include_extensions: Optional[List[str]],
            exclude_patterns: Optional[List[str]] = None
    ) -> List[Path]:
        """Get all files in directory matching criteria."""
        pattern = "**/*" if recursive else "*"
        files = []

        for file in dir_path.glob(pattern):
            if file.is_file() and not self._should_exclude(file, exclude_patterns):
                if include_extensions:
                    if any(file.name.endswith(ext) for ext in include_extensions):
                        files.append(file)
                else:
                    files.append(file)

        return files

    def _read_file_content(self, path: Path) -> str:
        """Read and return file content, handling binary files."""
        try:
            # Try to read as text
            with path.open('r', encoding='utf-8') as f:
                content = f.read()
                # Basic binary check
                if '\0' in content:
                    return "[Binary file]"
                return content
        except UnicodeDecodeError:
            return "[Binary file]"
        except PermissionError:
            raise FileAccessError(f"Permission denied: {path}")
        except Exception as e:
            raise FileAccessError(f"Error reading file: {str(e)}")

    def _format_file_content(self, rel_path: str, file_path: Path, format: ContentFormat) -> str:
        """Format content of a single file."""
        try:
            content = self._read_file_content(file_path)
            if format == ContentFormat.MARKDOWN:
                if content == "[Binary file]":
                    return f"## {rel_path}\n{content}"
                else:
                    return f"## {rel_path}\n```python\n{content}\n```"
            else:  # PLAIN
                return f"--- {rel_path} ---\n{content}"
        except FileAccessError as e:
            raise FileAccessError(f"Error reading file {rel_path}: {str(e)}")
