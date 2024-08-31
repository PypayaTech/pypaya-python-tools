import os
from enum import Enum
from typing import List, Optional


class OutputFormat(Enum):
    PLAIN = 1
    TREE = 2
    CONTENT = 3


def get_directory_structure(path, include_extensions=None, exclude_extensions=None, include_empty_directories=True):
    def traverse(current_path, indent=''):
        result = []
        items = sorted(os.listdir(current_path))
        for item in items:
            item_path = os.path.join(current_path, item)
            if os.path.isdir(item_path):
                sub_items = traverse(item_path, indent + '  ')
                if sub_items or include_empty_directories:
                    result.append(f"{indent}{item}/")
                    result.extend(sub_items)
            else:
                _, ext = os.path.splitext(item)
                ext = ext.lower()
                if include_extensions and ext not in include_extensions:
                    continue
                if exclude_extensions and ext in exclude_extensions:
                    continue
                result.append(f"{indent}{item}")
        return result

    return '\n'.join(traverse(path))


class DirectoryStructureGenerator:
    def __init__(self, root_path: str):
        self.root_path = root_path

    def generate(self, output_format: OutputFormat = OutputFormat.PLAIN, include_extensions: Optional[List[str]] = None,
                 exclude_extensions: Optional[List[str]] = None, include_empty_directories: bool = True) -> str:
        if include_extensions:
            include_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in
                                  include_extensions]
        if exclude_extensions:
            exclude_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in
                                  exclude_extensions]

        if output_format == OutputFormat.PLAIN:
            return self._generate_plain(include_extensions, exclude_extensions, include_empty_directories)
        elif output_format == OutputFormat.TREE:
            return self._generate_tree(include_extensions, exclude_extensions, include_empty_directories)
        elif output_format == OutputFormat.CONTENT:
            return self._generate_content(include_extensions, exclude_extensions, include_empty_directories)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_plain(self, include_extensions, exclude_extensions, include_empty_directories) -> str:
        return get_directory_structure(self.root_path, include_extensions, exclude_extensions,
                                       include_empty_directories)

    def _generate_tree(self, include_extensions, exclude_extensions, include_empty_directories) -> str:
        def traverse(path: str, prefix: str = '') -> List[str]:
            result = []
            items = sorted(os.listdir(path))
            filtered_items = [item for item in items if
                              self._should_include_item(item, include_extensions, exclude_extensions) or os.path.isdir(
                                  os.path.join(path, item))]
            for i, item in enumerate(filtered_items):
                item_path = os.path.join(path, item)
                is_last = i == len(filtered_items) - 1
                if os.path.isdir(item_path):
                    sub_items = traverse(item_path, prefix + ('    ' if is_last else '│   '))
                    if sub_items or include_empty_directories:
                        result.append(f"{prefix}{'└── ' if is_last else '├── '}{item}")
                        result.extend(sub_items)
                else:
                    result.append(f"{prefix}{'└── ' if is_last else '├── '}{item}")
            return result

        return '\n'.join([self.root_path] + traverse(self.root_path))

    def _generate_content(self, include_extensions, exclude_extensions, include_empty_directories) -> str:
        def traverse(path: str, relative_path: str = '') -> List[str]:
            result = []
            items = sorted(os.listdir(path))
            for item in items:
                item_path = os.path.join(path, item)
                item_relative_path = os.path.join(relative_path, item).replace('\\', '/')
                if os.path.isdir(item_path):
                    sub_items = traverse(item_path, item_relative_path)
                    if sub_items or include_empty_directories:
                        if item == '__pycache__':
                            result.append(f"\n## {item_relative_path}/ (skipped)\n")
                        else:
                            result.append(f"\n## {item_relative_path}/\n")
                            result.extend(sub_items)
                elif self._should_include_item(item, include_extensions, exclude_extensions):
                    result.append(f"\n### {item_relative_path}\n")
                    result.append("```\n")
                    try:
                        with open(item_path, 'r', encoding='utf-8') as f:
                            content = f.read().rstrip()
                        result.append(content)
                    except UnicodeDecodeError:
                        result.append(f"[Binary file or non-UTF-8 encoded text: {item}]")
                    except Exception as e:
                        result.append(f"[Error reading file: {str(e)}]")
                    result.append("\n```\n")
            return result

        structure = f"# Directory Structure\n\n```\n{self._generate_plain(include_extensions, exclude_extensions, include_empty_directories)}\n```\n"
        content = "\n# File Contents\n"
        content += ''.join(traverse(self.root_path))
        return structure + content

    @staticmethod
    def _should_include_item(item: str, include_extensions: Optional[List[str]],
                             exclude_extensions: Optional[List[str]]) -> bool:
        _, ext = os.path.splitext(item)
        ext = ext.lower()
        if include_extensions and ext not in include_extensions:
            return False
        if exclude_extensions and ext in exclude_extensions:
            return False
        return True


def generate_directory_structure(path: str, output_format: OutputFormat = OutputFormat.PLAIN,
                                 include_extensions: Optional[List[str]] = None,
                                 exclude_extensions: Optional[List[str]] = None,
                                 include_empty_directories: bool = True) -> str:
    generator = DirectoryStructureGenerator(path)
    return generator.generate(output_format, include_extensions, exclude_extensions, include_empty_directories)
