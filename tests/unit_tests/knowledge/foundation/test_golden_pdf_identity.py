"""Golden PDF preserves source identity without fabricating extracted text."""

from __future__ import annotations

from pathlib import Path

from knowledge.ingestion import IngestionArtifactRef, IngestionRequest, SourceFormat
from knowledge.ingestion_adapters import PdfIngestionAdapter
from knowledge.source import InMemorySourceVault, VaultArtifact, VaultArtifactMetadata
from knowledge.source.integrity import sha256_bytes_digest

_GOLDEN = Path(__file__).resolve().parents[3] / "fixtures" / "knowledge" / "golden" / "regenerative_cooling.pdf"


def test_golden_pdf_is_stored_without_fake_text() -> None:
    content = _GOLDEN.read_bytes()
    assert content.startswith(b"%PDF-")
    digest = sha256_bytes_digest(content)
    vault = InMemorySourceVault()
    vault.store(
        VaultArtifact(
            source_id="SRC-GOLDEN-PDF",
            artifact_id="ART-GOLDEN-PDF",
            content=content,
            content_hash=digest,
            metadata=VaultArtifactMetadata(source_format=SourceFormat.PDF.value),
        ),
    )
    adapter = PdfIngestionAdapter(vault)
    result = adapter.ingest(
        IngestionRequest(
            artifact=IngestionArtifactRef(
                source_id="SRC-GOLDEN-PDF",
                artifact_id="ART-GOLDEN-PDF",
                source_format=SourceFormat.PDF,
                content_hash=digest,
            ),
            adapter_name=adapter.adapter_name,
            adapter_version=adapter.adapter_version,
        ),
    )
    assert result.normalized_content_hash
    assert result.normalized_format.value == "STRUCTURED_TEXT"
    assert result.stage.value == "NORMALIZED"
