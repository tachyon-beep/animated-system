"""Unit tests for ecosystem tools module."""

import ast
import tempfile
from pathlib import Path

import pytest

from pyshort.ecosystem.tools import CodebaseExplorer, MethodImplementation, ClassDetails


class TestParentTracking:
    """Test parent context tracking for AST nodes."""

    def test_find_parent_context_returns_class_method(self, tmp_path):
        """_find_parent_context should return class.method for nodes inside methods."""
        source = '''
class MyClass:
    def my_method(self):
        x = SomeClass()  # Target node
'''
        test_file = tmp_path / "test_parent.py"
        test_file.write_text(source)

        explorer = CodebaseExplorer(test_file)
        tree = ast.parse(source)

        # Find the Call node (SomeClass())
        call_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_node = node
                break

        assert call_node is not None
        result = explorer._find_parent_context(tree, call_node)
        assert result == "MyClass.my_method"

    def test_find_parent_context_top_level_returns_none(self, tmp_path):
        """_find_parent_context should return None for top-level nodes."""
        source = '''
x = SomeClass()  # Top level
'''
        test_file = tmp_path / "test_parent.py"
        test_file.write_text(source)

        explorer = CodebaseExplorer(test_file)
        tree = ast.parse(source)

        # Find the Call node
        call_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_node = node
                break

        result = explorer._find_parent_context(tree, call_node)
        assert result is None
