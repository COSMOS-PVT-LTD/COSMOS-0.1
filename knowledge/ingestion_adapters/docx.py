"""DOCX ingestion adapter (NEW KG-010)."""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile

from knowledge.ingestion.models import (
    IngestionRequest,
    IngestionResult,
    NormalizedDocumentFormat,
    SourceFormat,
)
from knowledge.ingestion_adapters.base import VaultBackedAdapter
from knowledge.ingestion_adapters.exceptions import AdapterExecutionError
from knowledge.ingestion_adapters.normalize import build_structured_text_envelope
from knowledge.source.vault import SourceVault

__all__ = ("DocxIngestionAdapter",)

_W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _extract_docx_paragraphs(content: bytes) -> tuple[str, ...]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise AdapterExecutionError("DOCX artifact is not a valid ZIP archive.") from exc

    try:
        document_xml = archive.read("word/document.xml")
    except KeyError as exc:
        raise AdapterExecutionError(
            "DOCX artifact is missing word/document.xml."
        ) from exc

    root = ET.fromstring(document_xml)
    paragraphs: list[str] = []

    for paragraph in root.iter(f"{_W_NS}p"):
        texts = [
            node.text
            for node in paragraph.iter(f"{_W_NS}t")
            if node.text
        ]

        if texts:
            paragraphs.append("".join(texts))

    return tuple(paragraphs)


class DocxIngestionAdapter(VaultBackedAdapter):
    """DOCX ingestion preserving paragraph ordering."""

    def __init__(self, vault: SourceVault) -> None:
        super().__init__(
            vault,
            adapter_name="cosmos-docx-ingestion",
            adapter_version="0.1.0",
            supported_formats=frozenset({SourceFormat.DOCX}),
            parser_version="cosmos-docx-ingestion-0.1.0",
        )

    def ingest(self, request: IngestionRequest) -> IngestionResult:
        content = self._load_verified_content(request)
        self._require_format(request.artifact, SourceFormat.DOCX)

        paragraphs = _extract_docx_paragraphs(content)
        envelope = build_structured_text_envelope(
            {
                "format": "DOCX",
                "paragraphs": list(paragraphs),
            },
        )

        return self._build_result(
            request,
            envelope,
            normalized_format=NormalizedDocumentFormat.STRUCTURED_TEXT,
        )
