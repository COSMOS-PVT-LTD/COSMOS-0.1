"""HTML export."""

from __future__ import annotations

from html import escape
from typing import Any

from knowledge.exporters.markdown_exporter import export_markdown

__all__ = ("export_html",)


def export_html(payload: dict[str, Any]) -> str:
    markdown = export_markdown(payload)
    return f"<pre>{escape(markdown)}</pre>\n"
