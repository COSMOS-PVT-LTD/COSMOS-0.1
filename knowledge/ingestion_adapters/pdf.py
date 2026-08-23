"""PDF ingestion adapter (NEW KG-009)."""

from __future__ import annotations

from knowledge.ingestion.models import (
    IngestionRequest,
    IngestionResult,
    NormalizedDocumentFormat,
    SourceFormat,
)
from knowledge.ingestion_adapters.base import VaultBackedAdapter
from knowledge.ingestion_adapters.exceptions import UnsupportedContentError
from knowledge.ingestion_adapters.normalize import build_binary_envelope
from knowledge.source.integrity import sha256_bytes_digest
from knowledge.source.vault import SourceVault

__all__ = ("PdfIngestionAdapter",)


class PdfIngestionAdapter(VaultBackedAdapter):
    """
    PDF ingestion adapter.

    Verifies integrity and produces a deterministic structured envelope.
    Does not perform OCR or claim text extraction from binary PDFs.
    """

    def __init__(self, vault: SourceVault) -> None:
        super().__init__(
            vault,
            adapter_name="cosmos-pdf-ingestion",
            adapter_version="0.1.0",
            supported_formats=frozenset({SourceFormat.PDF}),
            parser_version="cosmos-pdf-ingestion-0.1.0",
        )

    def ingest(self, request: IngestionRequest) -> IngestionResult:
        content = self._load_verified_content(request)
        self._require_format(request.artifact, SourceFormat.PDF)

        if content.startswith(b"%PDF-"):
            envelope = build_binary_envelope(
                format_name="PDF",
                byte_length=len(content),
                content_hash=sha256_bytes_digest(content),
                text_available=False,
                notes="Binary PDF stored for downstream parsing.",
            )

            return self._build_result(
                request,
                envelope,
                normalized_format=NormalizedDocumentFormat.STRUCTURED_TEXT,
            )

        try:
            outline_text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UnsupportedContentError(
                "PDF artifact is neither a PDF header nor UTF-8 text."
            ) from exc

        return self._build_result(
            request,
            outline_text,
            normalized_format=NormalizedDocumentFormat.MARKDOWN,
        )
