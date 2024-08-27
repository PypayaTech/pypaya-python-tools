import pytest
import ast
import os
import tempfile
from pypaya_python_tools.code_manipulation.logging import LoggingTransformer, process_file
import re


def test_add_logging():
    code = """
def example_function(x, y):
    z = x + y
    return z
"""
    tree = ast.parse(code)
    transformer = LoggingTransformer()
    new_tree = transformer.visit(tree)
    new_code = ast.unparse(new_tree)

    expected_code = """
def example_function(x, y):
    logger.info("Entering function example_function")
    logger.info("Assigning to variable z")
    z = x + y
    logger.info("Returning from function")
    return z
    logger.info("Exiting function example_function")
"""

    # Remove whitespace and newlines for comparison
    new_code_normalized = re.sub(r'\s+', '', new_code)
    expected_code_normalized = re.sub(r'\s+', '', expected_code)

    # Replace all quotes with a common character for comparison
    new_code_normalized = re.sub(r'[\'"]', '"', new_code_normalized)
    expected_code_normalized = re.sub(r'[\'"]', '"', expected_code_normalized)

    assert new_code_normalized == expected_code_normalized, f"Expected:\n{expected_code}\n\nActual:\n{new_code}"


def test_remove_logging():
    code = """
def example_function(x, y):
    logger.info("Entering function example_function")
    z = x + y
    logger.info("Returning from function")
    return z
"""
    tree = ast.parse(code)
    transformer = LoggingTransformer(remove=True)
    new_tree = transformer.visit(tree)
    new_code = ast.unparse(new_tree)

    assert "logger.info" not in new_code


def test_exclude_function():
    code = """
def included_function():
    pass

def excluded_function():
    pass
"""
    tree = ast.parse(code)
    transformer = LoggingTransformer(excluded_functions={'excluded_function'})
    new_tree = transformer.visit(tree)
    new_code = ast.unparse(new_tree)

    assert "Entering function included_function" in new_code
    assert "Entering function excluded_function" not in new_code


def test_process_file():
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as tmp:
        tmp.write("""
def example_function():
    pass
""")
        tmp_name = tmp.name

    try:
        process_file(tmp_name, 'DEBUG', False, set(), '%(message)s', None)

        with open(tmp_name, 'r') as f:
            content = f.read()

        expected_content = '''
import logging

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

def example_function():
    logger.debug('Entering function example_function')
    pass
    logger.debug('Exiting function example_function')
'''
        # Normalize whitespace and newlines
        content = '\n'.join(line.strip() for line in content.strip().splitlines())
        expected_content = '\n'.join(line.strip() for line in expected_content.strip().splitlines())

        assert content == expected_content, f"Expected:\n{expected_content}\n\nActual:\n{content}"
    finally:
        os.unlink(tmp_name)


def test_log_format_and_file():
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as tmp:
        tmp.write("""
def example_function():
    pass
""")
        tmp_name = tmp.name

    log_file = 'test.log'
    try:
        process_file(tmp_name, 'INFO', False, set(), '%(levelname)s: %(message)s', log_file)

        with open(tmp_name, 'r') as f:
            content = f.read()

        assert "formatter = logging.Formatter('%(levelname)s: %(message)s')" in content
        assert f"handler = logging.FileHandler('{log_file}')" in content
    finally:
        os.unlink(tmp_name)
        if os.path.exists(log_file):
            os.unlink(log_file)
