import pytest
from pypaya_python_tools.coding_with_llms.formats import StructureFormat, ContentFormat


def test_structure_format_values():
    assert set(StructureFormat) == {
        StructureFormat.PLAIN,
        StructureFormat.TREE,
        StructureFormat.MARKDOWN
    }

def test_content_format_values():
    assert set(ContentFormat) == {
        ContentFormat.MARKDOWN,
        ContentFormat.PLAIN
    }
