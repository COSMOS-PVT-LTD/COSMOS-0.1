"""LaTeX loader — ingest as text via the Markdown adapter."""

from __future__ import annotations

from pathlib import Path

from knowledge.compat.ingestion_loaders import ingest_file_from_path
from knowledge.ingestion.models import IngestionResult, SourceFormat
from knowledge.ingestion_adapters.html import MarkdownIngestionAdapter
from knowledge.source import InMemorySourceVault

__all__ = ("load_latex",)


def load_latex(path: str | Path) -> IngestionResult:
    vault = InMemorySourceVault()
    return ingest_file_from_path(
        path,
        source_format=SourceFormat.MARKDOWN,
        adapter=MarkdownIngestionAdapter(vault),
        vault=vault,
    )
