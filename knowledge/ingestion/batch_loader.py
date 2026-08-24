"""Batch ingestion over existing adapters."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from knowledge.compat.ingestion_loaders import ingest_file_from_path
from knowledge.ingestion.models import IngestionResult, SourceFormat
from knowledge.ingestion_adapters.html import MarkdownIngestionAdapter
from knowledge.source import InMemorySourceVault

__all__ = ("load_markdown_batch",)


def load_markdown_batch(paths: Iterable[str | Path]) -> tuple[IngestionResult, ...]:
    vault = InMemorySourceVault()
    adapter = MarkdownIngestionAdapter(vault)
    results: list[IngestionResult] = []
    for index, path in enumerate(paths):
        results.append(
            ingest_file_from_path(
                path,
                source_format=SourceFormat.MARKDOWN,
                adapter=adapter,
                vault=vault,
                source_id=f"SRC-BATCH-{index:04d}",
                artifact_id=f"ART-BATCH-{index:04d}",
            ),
        )
    return tuple(results)
