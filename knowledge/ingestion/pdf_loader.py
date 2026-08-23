"""
COMPATIBILITY FACADE (KG-BLOCK-013 Phase B — COMPAT-001).

Frozen Part-3 path delegating to canonical PdfIngestionAdapter.
"""

from __future__ import annotations

from pathlib import Path

from knowledge.compat.ingestion_loaders import ingest_file_from_path
from knowledge.ingestion.models import IngestionResult, SourceFormat
from knowledge.ingestion_adapters.pdf import PdfIngestionAdapter
from knowledge.source import InMemorySourceVault

__all__ = ("load_pdf",)


def load_pdf(
    path: str | Path,
    *,
    vault: InMemorySourceVault | None = None,
    source_id: str | None = None,
    artifact_id: str | None = None,
) -> IngestionResult:
    """Load a PDF from a local path via the canonical ingestion adapter."""

    active_vault = vault or InMemorySourceVault()
    adapter = PdfIngestionAdapter(active_vault)

    return ingest_file_from_path(
        path,
        source_format=SourceFormat.PDF,
        adapter=adapter,
        vault=active_vault,
        source_id=source_id,
        artifact_id=artifact_id,
    )
