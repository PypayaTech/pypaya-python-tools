import ast
from typing import List, Optional, Set

from pypaya_python_tools.code_analysis.base import CodeSecurityAnalyzer, SecurityViolation


class NameAccessAnalyzer(CodeSecurityAnalyzer):
    """
    Controls access to global names

    Analyzes code to determine what global variables, functions, or
    classes it attempts to access, and validates against allowed lists.
    """

    def __init__(self,
                 allowed_names: Optional[Set[str]] = None,
                 blocked_names: Optional[Set[str]] = None,
                 check_attributes: bool = True):
        """
        Initialize with name restrictions

        Args:
            allowed_names: Set of global names that can be accessed
            blocked_names: Set of global names that cannot be accessed
            check_attributes: Whether to check attribute access (obj.attr)
        """
        self.allowed_names = allowed_names or set()
        self.blocked_names = blocked_names or set()
        self.check_attributes = check_attributes

    def analyze(self, code: str) -> List[SecurityViolation]:
        """
        Analyze code for unauthorized name usage

        Args:
            code: Python code as string

        Returns:
            List of SecurityViolation objects
        """
        violations = []

        try:
            # Parse the code into an AST
            tree = ast.parse(code)

            # Create a name visitor
            visitor = NameVisitor(
                allowed_names=self.allowed_names,
                blocked_names=self.blocked_names,
                check_attributes=self.check_attributes
            )
            visitor.visit(tree)

            # Collect violations
            violations.extend(visitor.violations)

        except SyntaxError as e:
            violations.append(
                SecurityViolation(
                    f"Syntax error: {str(e)}",
                    line=e.lineno,
                    column=e.offset
                )
            )

        return violations


class NameVisitor(ast.NodeVisitor):
    """AST visitor that collects name usage"""

    def __init__(self, allowed_names, blocked_names, check_attributes):
        self.allowed_names = allowed_names
        self.blocked_names = blocked_names
        self.check_attributes = check_attributes
        self.violations = []
        self.defined_names = set()  # Names defined in the code

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Register function names as locally defined"""
        self.defined_names.add(node.name)
        # Also add arguments to defined_names as they are local to the function scope
        for arg in node.args.args:
            self.defined_names.add(arg.arg)
        # Continue visiting the children of this node (e.g., the function body)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Register class names as locally defined"""
        self.defined_names.add(node.name)
        # Continue visiting the children of this node (e.g., methods)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        """Register imported module names as defined"""
        for alias in node.names:
            self.defined_names.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Register names from 'from ... import' as defined"""
        for alias in node.names:
            self.defined_names.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        """Check variable and function name usage"""
        if isinstance(node.ctx, ast.Load):
            # This is a name being used, not defined
            name = node.id

            # Skip names defined within the code snippet itself
            if name in self.defined_names:
                return

            # Skip built-in dunder names
            if name.startswith('__') and name.endswith('__'):
                return

            # Check if blocked
            if name in self.blocked_names:
                self.violations.append(
                    SecurityViolation(
                        f"Use of blocked name: '{name}'",
                        line=node.lineno,
                        column=node.col_offset
                    )
                )

            # Check if not allowed (if we have an allowlist)
            elif self.allowed_names and name not in self.allowed_names:
                self.violations.append(
                    SecurityViolation(
                        f"Use of unauthorized name: '{name}'",
                        line=node.lineno,
                        column=node.col_offset
                    )
                )

        elif isinstance(node.ctx, ast.Store):
            # This is a name being defined via assignment
            self.defined_names.add(node.id)

    def visit_Attribute(self, node: ast.Attribute):
        """Check attribute access"""
        if not self.check_attributes:
            self.generic_visit(node)
            return

        if isinstance(node.value, ast.Name):
            obj_name = node.value.id
            attr_name = node.attr

            # TODO Should this be defined like this? Either remove or make constants somewhere
            dangerous_patterns = {
                'os': ['system', 'popen', 'execve', 'spawn', 'fork', 'remove', 'rmdir', 'unlink'],
                'subprocess': ['call', 'Popen', 'run'],
                'sys': ['modules', 'exit'],
            }

            if obj_name in dangerous_patterns and attr_name in dangerous_patterns[obj_name]:
                self.violations.append(
                    SecurityViolation(
                        f"Potentially dangerous attribute access: '{obj_name}.{attr_name}'",
                        line=node.lineno,
                        column=node.col_offset
                    )
                )

        # Always continue visiting children to catch nested issues
        self.generic_visit(node)
