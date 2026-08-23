"""
Parse input context bridging ingestion results to W3 parsers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from knowledge.ingestion.models import IngestionResult, NormalizedDocumentFormat
from knowledge.parsers.w3.exceptions import ParserContentError
from knowledge.source.integrity import sha256_text_digest, verify_digest

if TYPE_CHECKING:
    from knowledge.parsers.w3.models import StructuredParsedDocument

__all__ = (
    "ParseContext",
    "ParseResult",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ParseContext:
    """
    Bounded parse input combining a frozen ingestion result with normalized text.

    Normalized content is supplied by the caller (vault resolution or adapter
    output) because IngestionResult carries hash metadata only.
    """

    ingestion_result: IngestionResult
    normalized_content: str

    def __post_init__(self) -> None:
        if not isinstance(self.ingestion_result, IngestionResult):
            raise ParserContentError(
                "ingestion_result must be an IngestionResult instance."
            )

        if not isinstance(self.normalized_content, str):
            raise ParserContentError("normalized_content must be a string.")

    @property
    def document_id(self) -> str:
        artifact = self.ingestion_result.request.artifact

        return self.ingestion_result.document_id or artifact.artifact_id

    @property
    def source_id(self) -> str:
        return self.ingestion_result.request.artifact.source_id

    @property
    def artifact_id(self) -> str:
        return self.ingestion_result.request.artifact.artifact_id

    @property
    def normalized_format(self) -> NormalizedDocumentFormat:
        return self.ingestion_result.normalized_format

    def verify_content_hash(self) -> None:
        """Raise when normalized content does not match the ingestion hash."""

        verify_digest(
            self.normalized_content.encode("utf-8"),
            self.ingestion_result.normalized_content_hash,
        )

    def content_digest(self) -> str:
        """Return the SHA-256 digest of normalized content."""

        return sha256_text_digest(self.normalized_content)


@dataclass(frozen=True, slots=True, kw_only=True)
class ParseResult:
    """Complete W3 parse output with stage-advanced ingestion metadata."""

    parsed_document: "StructuredParsedDocument"
    ingestion_result: IngestionResult

    def __post_init__(self) -> None:
        from knowledge.parsers.w3.models import StructuredParsedDocument

        if not isinstance(self.parsed_document, StructuredParsedDocument):
            raise ParserContentError(
                "parsed_document must be a StructuredParsedDocument instance."
            )

        if not isinstance(self.ingestion_result, IngestionResult):
            raise ParserContentError(
                "ingestion_result must be an IngestionResult instance."
            )
