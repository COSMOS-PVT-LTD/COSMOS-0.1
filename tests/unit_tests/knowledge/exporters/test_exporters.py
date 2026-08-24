"""Export provenance tests."""

from __future__ import annotations

import pytest

from knowledge.exporters.json_exporter import export_json
from knowledge.exporters.markdown_exporter import export_markdown


def test_json_export_requires_provenance() -> None:
    with pytest.raises(ValueError):
        export_json({"name": "Bartz"})


def test_markdown_export_includes_provenance() -> None:
    text = export_markdown({"name": "Bartz", "provenance": "REF-NASA", "equation": "h=f(Re)"})
    assert "Provenance" in text
    assert "Bartz" in text
