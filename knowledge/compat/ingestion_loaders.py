"""Shared ingestion loader delegation for frozen-path compatibility facades."""

from __future__ import annotations

from pathlib import Path

from knowledge.ingestion.base import IngestionAdapter
from knowledge.ingestion.models import (
    IngestionArtifactRef,
    IngestionRequest,
    IngestionResult,
    SourceFormat,
)
from knowledge.source import InMemorySourceVault, VaultArtifact, VaultArtifactMetadata
from knowledge.source.integrity import sha256_bytes_digest

__all__ = ("ingest_file_from_path",)


def _deterministic_ids(path: Path) -> tuple[str, str]:
    digest = sha256_bytes_digest(str(path.resolve()).encode("utf-8"))
    return f"SRC-{digest[:16]}", f"ART-{digest[16:32]}"


def ingest_file_from_path(
    path: str | Path,
    *,
    source_format: SourceFormat,
    adapter: IngestionAdapter,
    vault: InMemorySourceVault | None = None,
    source_id: str | None = None,
    artifact_id: str | None = None,
) -> IngestionResult:
    """Load a local file into the vault and delegate ingestion to a canonical adapter."""

    file_path = Path(path)

    if not file_path.is_file():
        msg = f"ingestion path does not exist or is not a file: {file_path}"
        raise FileNotFoundError(msg)

    content = file_path.read_bytes()
    content_hash = sha256_bytes_digest(content)
    default_source_id, default_artifact_id = _deterministic_ids(file_path)
    resolved_source_id = source_id or default_source_id
    resolved_artifact_id = artifact_id or default_artifact_id

    active_vault = vault or InMemorySourceVault()
    active_vault.store(
        VaultArtifact(
            source_id=resolved_source_id,
            artifact_id=resolved_artifact_id,
            content=content,
            content_hash=content_hash,
            metadata=VaultArtifactMetadata(
                source_format=source_format.value,
            ),
        ),
    )

    artifact = IngestionArtifactRef(
        source_id=resolved_source_id,
        artifact_id=resolved_artifact_id,
        source_format=source_format,
        content_hash=content_hash,
    )

    return adapter.ingest(
        IngestionRequest(
            artifact=artifact,
            adapter_name=adapter.adapter_name,
            adapter_version=adapter.adapter_version,
        ),
    )
