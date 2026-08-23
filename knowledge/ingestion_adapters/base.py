"""
COSMOS Knowledge Foundation

Module:
    knowledge.ingestion_adapters.base

Purpose:
    Shared adapter utilities for vault-backed ingestion.
"""

from __future__ import annotations

from typing import cast

from knowledge.ingestion.base import IngestionAdapter, validate_adapter_request
from knowledge.ingestion.models import (
    IngestionArtifactRef,
    IngestionRequest,
    IngestionResult,
    IngestionStage,
    NormalizedDocumentFormat,
    SourceFormat,
)
from knowledge.ingestion_adapters.exceptions import AdapterValidationError
from knowledge.ingestion_adapters.normalize import build_normalized_result_fields
from knowledge.source.integrity import verify_digest
from knowledge.source.vault import SourceVault

__all__ = (
    "VaultBackedAdapter",
)


class VaultBackedAdapter:
    """Base helper for adapters that read artifact bytes from a source vault."""

    def __init__(
        self,
        vault: SourceVault,
        *,
        adapter_name: str,
        adapter_version: str,
        supported_formats: frozenset[SourceFormat],
        parser_version: str,
    ) -> None:
        self._vault = vault
        self._adapter_name = adapter_name
        self._adapter_version = adapter_version
        self._supported_formats = supported_formats
        self._parser_version = parser_version

    @property
    def adapter_name(self) -> str:
        return self._adapter_name

    @property
    def adapter_version(self) -> str:
        return self._adapter_version

    @property
    def supported_formats(self) -> frozenset[SourceFormat]:
        return self._supported_formats

    def can_ingest(self, artifact: IngestionArtifactRef) -> bool:
        return artifact.source_format in self._supported_formats

    def _load_verified_content(self, request: IngestionRequest) -> bytes:
        validate_adapter_request(cast(IngestionAdapter, self), request)

        artifact = request.artifact
        vault_artifact = self._vault.retrieve(
            artifact.source_id,
            artifact.artifact_id,
        )

        if artifact.content_hash is not None:
            verify_digest(vault_artifact.content, artifact.content_hash)
        elif vault_artifact.content_hash:
            verify_digest(vault_artifact.content, vault_artifact.content_hash)

        return vault_artifact.content

    def _build_result(
        self,
        request: IngestionRequest,
        normalized_text: str,
        *,
        normalized_format: NormalizedDocumentFormat,
    ) -> IngestionResult:
        fmt, content_hash, parser_version = build_normalized_result_fields(
            normalized_text,
            normalized_format=normalized_format,
            parser_version=self._parser_version,
        )

        return IngestionResult(
            request=request,
            normalized_format=fmt,
            normalized_content_hash=content_hash,
            parser_version=parser_version,
            stage=IngestionStage.NORMALIZED,
            document_id=request.artifact.artifact_id,
        )

    def _require_format(
        self,
        artifact: IngestionArtifactRef,
        expected: SourceFormat,
    ) -> None:
        if artifact.source_format is not expected:
            raise AdapterValidationError(
                f"Expected source format {expected.value}."
            )
