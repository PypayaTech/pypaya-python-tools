import ast
from typing import List, Optional, Set, Dict, Any

from pypaya_python_tools.code_analysis.base import CodeSecurityAnalyzer, SecurityViolation


class ImportAnalyzer(CodeSecurityAnalyzer):
    """
    Analyzes code for unauthorized imports

    Parses code to extract all import statements and validates
    them against allowed and blocked lists.
    """

    def __init__(self,
                 allowed_modules: Optional[Set[str]] = None,
                 blocked_modules: Optional[Set[str]] = None,
                 allow_import_from: bool = True,
                 default_policy: str = "deny"):
        """
        Initialize import analyzer

        Args:
            allowed_modules: Set of module names that can be imported
            blocked_modules: Set of module names that cannot be imported
            allow_import_from: Whether to allow 'from x import y' syntax
            default_policy: 'allow' or 'deny' for modules not in either list
        """
        self.allowed_modules = allowed_modules or set()
        self.blocked_modules = blocked_modules or set()
        self.allow_import_from = allow_import_from

        if default_policy not in ("allow", "deny"):
            raise ValueError("default_policy must be 'allow' or 'deny'")
        self.default_policy = default_policy

    def analyze(self, code: str) -> List[SecurityViolation]:
        """
        Scan code for import violations

        Args:
            code: Python code as string

        Returns:
            List of SecurityViolation objects
        """
        violations = []

        try:
            # Parse the code into an AST
            tree = ast.parse(code)

            # Create an import visitor
            visitor = ImportVisitor()
            visitor.visit(tree)

            # Check each import against our rules
            for imp in visitor.imports:
                is_allowed = self._is_import_allowed(imp)

                if not is_allowed:
                    if imp["type"] == "import":
                        violations.append(
                            SecurityViolation(
                                f"Unauthorized import: '{imp['name']}'",
                                line=imp["lineno"],
                                column=imp["col_offset"]
                            )
                        )
                    elif imp["type"] == "importfrom":
                        if not self.allow_import_from:
                            violations.append(
                                SecurityViolation(
                                    f"'from ... import' syntax is not allowed: '{imp['module']}'",
                                    line=imp["lineno"],
                                    column=imp["col_offset"]
                                )
                            )
                        else:
                            violations.append(
                                SecurityViolation(
                                    f"Unauthorized import: 'from {imp['module']} import {imp['name']}'",
                                    line=imp["lineno"],
                                    column=imp["col_offset"]
                                )
                            )

        except SyntaxError as e:
            violations.append(
                SecurityViolation(
                    f"Syntax error: {str(e)}",
                    line=e.lineno,
                    column=e.offset
                )
            )

        return violations

    def _is_import_allowed(self, import_info: Dict[str, Any]) -> bool:
        """
        Check if an import is allowed according to our rules

        Args:
            import_info: Dictionary with import information

        Returns:
            True if the import is allowed, False otherwise
        """
        # First check if "from ... import" syntax is allowed
        if not self.allow_import_from and import_info["type"] == "importfrom":
            return False

        module_name = import_info["module"] if import_info["type"] == "importfrom" else import_info["name"]

        # Check if the module is explicitly blocked
        if module_name in self.blocked_modules:
            return False

        # Check if the module is explicitly allowed
        if module_name in self.allowed_modules:
            return True

        # Apply default policy for modules not explicitly listed
        return self.default_policy == "allow"


class ImportVisitor(ast.NodeVisitor):
    """AST visitor that collects import statements"""

    def __init__(self):
        self.imports = []

    def visit_Import(self, node):
        """Process 'import x' statements"""
        for name in node.names:
            self.imports.append({
                "type": "import",
                "name": name.name,
                "asname": name.asname,
                "lineno": node.lineno,
                "col_offset": node.col_offset
            })

    def visit_ImportFrom(self, node):
        """Process 'from x import y' statements"""
        module = node.module or ""
        for name in node.names:
            self.imports.append({
                "type": "importfrom",
                "module": module,
                "name": name.name,
                "asname": name.asname,
                "lineno": node.lineno,
                "col_offset": node.col_offset
            })
