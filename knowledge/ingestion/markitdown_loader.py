"""MarkItDown loader — canonical Markdown ingestion path."""

from __future__ import annotations

from pathlib import Path

from knowledge.ingestion.markdown_loader import load_markdown
from knowledge.ingestion.models import IngestionResult

__all__ = ("load_markitdown",)


def load_markitdown(path: str | Path) -> IngestionResult:
    return load_markdown(path)
