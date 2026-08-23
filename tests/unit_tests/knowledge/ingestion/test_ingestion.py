"""Unit tests for knowledge.ingestion contracts."""

from __future__ import annotations

import pytest

from knowledge.ingestion import (
    IngestionAdapterError,
    IngestionArtifactRef,
    IngestionRequest,
    IngestionResult,
    IngestionStage,
    IngestionValidationError,
    NormalizedDocumentFormat,
    SourceFormat,
    supports_source_format,
    validate_adapter_request,
)

_VALID_SHA256 = "a" * 64


class _MarkdownAdapter:
    adapter_name = "markdown-adapter"
    adapter_version = "0.1.0"
    supported_formats = frozenset({SourceFormat.MARKDOWN})

    def can_ingest(self, artifact: IngestionArtifactRef) -> bool:
        return artifact.source_format in self.supported_formats

    def ingest(self, request: IngestionRequest) -> IngestionResult:
        validate_adapter_request(self, request)
        return IngestionResult(
            request=request,
            normalized_format=NormalizedDocumentFormat.MARKDOWN,
            normalized_content_hash=_VALID_SHA256,
            parser_version=self.adapter_version,
        )


def test_ingestion_artifact_ref_is_deterministic() -> None:
    """Artifact references must compare equal for identical inputs."""

    first = IngestionArtifactRef(
        source_id="SRC-001",
        artifact_id="ART-001",
        source_format=SourceFormat.PDF,
    )
    second = IngestionArtifactRef(
        source_id="SRC-001",
        artifact_id="ART-001",
        source_format=SourceFormat.PDF,
    )

    assert first == second
    assert first.identity_key() == second.identity_key()


def test_ingestion_artifact_ref_rejects_invalid_hash() -> None:
    """Invalid content hashes must be rejected."""

    with pytest.raises(IngestionValidationError):
        IngestionArtifactRef(
            source_id="SRC-001",
            artifact_id="ART-001",
            source_format=SourceFormat.PDF,
            content_hash="not-a-hash",
        )


def test_ingestion_result_requires_normalized_hash() -> None:
    """Ingestion results must include a normalized content hash."""

    artifact = IngestionArtifactRef(
        source_id="SRC-001",
        artifact_id="ART-001",
        source_format=SourceFormat.MARKDOWN,
    )
    request = IngestionRequest(
        artifact=artifact,
        adapter_name="markdown-adapter",
        adapter_version="0.1.0",
    )

    with pytest.raises(IngestionValidationError):
        IngestionResult(
            request=request,
            normalized_format=NormalizedDocumentFormat.MARKDOWN,
            normalized_content_hash="invalid",
            parser_version="0.1.0",
        )


def test_ingestion_adapter_contract_via_test_double() -> None:
    """Adapters must support format checks and ingestion requests."""

    adapter = _MarkdownAdapter()
    artifact = IngestionArtifactRef(
        source_id="SRC-001",
        artifact_id="ART-001",
        source_format=SourceFormat.MARKDOWN,
    )
    request = IngestionRequest(
        artifact=artifact,
        adapter_name="markdown-adapter",
        adapter_version="0.1.0",
    )

    assert supports_source_format(adapter, SourceFormat.MARKDOWN)
    result = adapter.ingest(request)

    assert result.stage is IngestionStage.NORMALIZED
    assert result.normalized_content_hash == _VALID_SHA256


def test_validate_adapter_request_rejects_format_mismatch() -> None:
    """Adapter validation must reject unsupported artifact formats."""

    adapter = _MarkdownAdapter()
    request = IngestionRequest(
        artifact=IngestionArtifactRef(
            source_id="SRC-001",
            artifact_id="ART-001",
            source_format=SourceFormat.PDF,
        ),
        adapter_name="markdown-adapter",
        adapter_version="0.1.0",
    )

    with pytest.raises(IngestionAdapterError):
        validate_adapter_request(adapter, request)
