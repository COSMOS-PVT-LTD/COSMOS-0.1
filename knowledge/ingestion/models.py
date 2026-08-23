"""
COSMOS Knowledge Foundation

Module:
    knowledge.ingestion.models

Purpose:
    Ingestion request/result contracts for document adapter pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.graph.source_identity import is_valid_sha256_hex
from knowledge.ingestion.exceptions import IngestionValidationError

__all__ = (
    "IngestionArtifactRef",
    "IngestionRequest",
    "IngestionResult",
    "IngestionStage",
    "NormalizedDocumentFormat",
    "SourceFormat",
)


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise IngestionValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise IngestionValidationError(f"{field_name} must not be blank.")

    return cleaned


def _validate_optional_non_empty_string(
    field_name: str,
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return _validate_non_empty_string(field_name, value)


def _validate_sha256(field_name: str, value: str) -> str:
    cleaned = _validate_non_empty_string(field_name, value)

    if not is_valid_sha256_hex(cleaned):
        raise IngestionValidationError(
            f"{field_name} must be a 64-character hexadecimal SHA-256 digest."
        )

    return cleaned.lower()


def _validate_optional_sha256(
    field_name: str,
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return _validate_sha256(field_name, value)


class SourceFormat(Enum):
    """Supported source artifact formats for ingestion adapters."""

    PDF = "PDF"
    DOCX = "DOCX"
    PPTX = "PPTX"
    XLSX = "XLSX"
    HTML = "HTML"
    MARKDOWN = "MARKDOWN"


class NormalizedDocumentFormat(Enum):
    """Normalized output formats produced by ingestion adapters."""

    MARKDOWN = "MARKDOWN"
    STRUCTURED_TEXT = "STRUCTURED_TEXT"


class IngestionStage(Enum):
    """High-level ingestion pipeline stage for an artifact."""

    REGISTERED = "REGISTERED"
    NORMALIZED = "NORMALIZED"
    PARSED = "PARSED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True, kw_only=True)
class IngestionArtifactRef:
    """
    Reference to a registered source artifact awaiting ingestion.

    Does not embed artifact content.
    """

    source_id: str
    artifact_id: str
    source_format: SourceFormat
    content_hash: str | None = None
    file_hash: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            _validate_non_empty_string("source_id", self.source_id),
        )
        object.__setattr__(
            self,
            "artifact_id",
            _validate_non_empty_string("artifact_id", self.artifact_id),
        )

        if not isinstance(self.source_format, SourceFormat):
            raise IngestionValidationError(
                "source_format must be a SourceFormat value."
            )

        object.__setattr__(
            self,
            "content_hash",
            _validate_optional_sha256("content_hash", self.content_hash),
        )
        object.__setattr__(
            self,
            "file_hash",
            _validate_optional_sha256("file_hash", self.file_hash),
        )

    def identity_key(self) -> tuple[str, str, str]:
        """Return the deterministic identity key for this artifact reference."""

        return (
            self.source_id,
            self.artifact_id,
            self.source_format.value,
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "source_id": self.source_id,
            "artifact_id": self.artifact_id,
            "source_format": self.source_format.value,
        }

        if self.content_hash is not None:
            payload["content_hash"] = self.content_hash
        if self.file_hash is not None:
            payload["file_hash"] = self.file_hash

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class IngestionRequest:
    """Request to ingest a registered source artifact through an adapter."""

    artifact: IngestionArtifactRef
    adapter_name: str
    adapter_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.artifact, IngestionArtifactRef):
            raise IngestionValidationError(
                "artifact must be an IngestionArtifactRef instance."
            )

        object.__setattr__(
            self,
            "adapter_name",
            _validate_non_empty_string("adapter_name", self.adapter_name),
        )
        object.__setattr__(
            self,
            "adapter_version",
            _validate_non_empty_string(
                "adapter_version",
                self.adapter_version,
            ),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "artifact": self.artifact.to_mapping(),
            "adapter_name": self.adapter_name,
            "adapter_version": self.adapter_version,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class IngestionResult:
    """
    Result of a successful ingestion adapter operation.

    Contains normalized representation metadata without embedding copyrighted
    source text in graph contracts.
    """

    request: IngestionRequest
    normalized_format: NormalizedDocumentFormat
    normalized_content_hash: str
    parser_version: str
    stage: IngestionStage = IngestionStage.NORMALIZED
    document_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.request, IngestionRequest):
            raise IngestionValidationError(
                "request must be an IngestionRequest instance."
            )

        if not isinstance(self.normalized_format, NormalizedDocumentFormat):
            raise IngestionValidationError(
                "normalized_format must be a NormalizedDocumentFormat value."
            )

        object.__setattr__(
            self,
            "normalized_content_hash",
            _validate_sha256(
                "normalized_content_hash",
                self.normalized_content_hash,
            ),
        )
        object.__setattr__(
            self,
            "parser_version",
            _validate_non_empty_string(
                "parser_version",
                self.parser_version,
            ),
        )

        if not isinstance(self.stage, IngestionStage):
            raise IngestionValidationError(
                "stage must be an IngestionStage value."
            )

        object.__setattr__(
            self,
            "document_id",
            _validate_optional_non_empty_string(
                "document_id",
                self.document_id,
            ),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "request": self.request.to_mapping(),
            "normalized_format": self.normalized_format.value,
            "normalized_content_hash": self.normalized_content_hash,
            "parser_version": self.parser_version,
            "stage": self.stage.value,
        }

        if self.document_id is not None:
            payload["document_id"] = self.document_id

        return payload
