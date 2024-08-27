import ast
import os
import argparse
import astor
import re


class LoggingTransformer(ast.NodeTransformer):
    def __init__(self, log_level='INFO', remove=False, excluded_functions=None):
        self.log_level = log_level
        self.remove = remove
        self.excluded_functions = excluded_functions or set()

    def visit_FunctionDef(self, node):
        if node.name in self.excluded_functions:
            return node

        if self.remove:
            node.body = [stmt for stmt in node.body if not self._is_log_stmt(stmt)]
        else:
            log_entry = self._create_log_stmt(f"Entering function {node.name}")
            log_exit = self._create_log_stmt(f"Exiting function {node.name}")
            node.body.insert(0, log_entry)
            node.body.append(log_exit)

        self.generic_visit(node)
        return node

    def visit_For(self, node):
        if not self.remove:
            log_stmt = self._create_log_stmt("Starting loop")
            node.body.insert(0, log_stmt)
        self.generic_visit(node)
        return node

    def visit_Return(self, node):
        if self.remove:
            return node
        log_stmt = self._create_log_stmt("Returning from function")
        return [log_stmt, node]

    def visit_Assign(self, node):
        if self.remove:
            return node
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            log_stmt = self._create_log_stmt(f"Assigning to variable {var_name}")
            return [log_stmt, node]
        return node

    def _create_log_stmt(self, message):
        return ast.Expr(ast.Call(
            func=ast.Attribute(
                value=ast.Name(id='logger', ctx=ast.Load()),
                attr=self.log_level.lower(),
                ctx=ast.Load()
            ),
            args=[ast.Str(s=message)],
            keywords=[]
        ))

    def _is_log_stmt(self, node):
        return (isinstance(node, ast.Expr) and
                isinstance(node.value, ast.Call) and
                isinstance(node.value.func, ast.Attribute) and
                isinstance(node.value.func.value, ast.Name) and
                node.value.func.value.id == 'logger')


def process_file(file_path, log_level, remove, excluded_functions, log_format, log_file):
    with open(file_path, 'r') as file:
        source = file.read()

    tree = ast.parse(source)
    transformer = LoggingTransformer(log_level, remove, excluded_functions)
    new_tree = transformer.visit(tree)

    new_source = astor.to_source(new_tree)

    if not remove:
        logging_setup = f"""
import logging

logger = logging.getLogger(__name__)
handler = logging.{'FileHandler' if log_file else 'StreamHandler'}({repr(log_file) if log_file else ''})
formatter = logging.Formatter({repr(log_format)})
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.{log_level})

"""
        new_source = logging_setup + new_source
    else:
        new_source = re.sub(r'import logging.*?\n\n', '', new_source, flags=re.DOTALL)

    with open(file_path, 'w') as file:
        file.write(new_source)


def process_directory(directory, log_level, remove, excluded_functions, log_format, log_file, excluded_files):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and file not in excluded_files:
                file_path = os.path.join(root, file)
                process_file(file_path, log_level, remove, excluded_functions, log_format, log_file)


def main():
    parser = argparse.ArgumentParser(description='Add or remove logging statements in Python code.')
    parser.add_argument('path', help='File or directory to process')
    parser.add_argument('--level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Logging level')
    parser.add_argument('--remove', action='store_true', help='Remove logging statements')
    parser.add_argument('--exclude-functions', nargs='*', default=[], help='Functions to exclude from logging')
    parser.add_argument('--exclude-files', nargs='*', default=[], help='Files to exclude from logging')
    parser.add_argument('--format', default='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        help='Logging format')
    parser.add_argument('--log-file', help='File to log to (if not specified, log to console)')
    args = parser.parse_args()

    if os.path.isfile(args.path):
        process_file(args.path, args.level, args.remove, set(args.exclude_functions),
                     args.format, args.log_file)
    elif os.path.isdir(args.path):
        process_directory(args.path, args.level, args.remove, set(args.exclude_functions),
                          args.format, args.log_file, set(args.exclude_files))
    else:
        print(f"Error: {args.path} is not a valid file or directory")


if __name__ == "__main__":
    main()
