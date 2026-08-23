"""PPTX ingestion adapter (NEW KG-011)."""

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

__all__ = ("PptxIngestionAdapter",)

_A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def _extract_pptx_slides(content: bytes) -> tuple[dict[str, object], ...]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise AdapterExecutionError("PPTX artifact is not a valid ZIP archive.") from exc

    slide_names = sorted(
        name
        for name in archive.namelist()
        if name.startswith("ppt/slides/slide") and name.endswith(".xml")
    )

    slides: list[dict[str, object]] = []

    for index, slide_name in enumerate(slide_names, start=1):
        root = ET.fromstring(archive.read(slide_name))
        texts = [
            node.text.strip()
            for node in root.iter(f"{_A_NS}t")
            if node.text and node.text.strip()
        ]

        slides.append(
            {
                "slide_number": index,
                "text_blocks": texts,
            },
        )

    return tuple(slides)


class PptxIngestionAdapter(VaultBackedAdapter):
    """PPTX ingestion preserving slide structure."""

    def __init__(self, vault: SourceVault) -> None:
        super().__init__(
            vault,
            adapter_name="cosmos-pptx-ingestion",
            adapter_version="0.1.0",
            supported_formats=frozenset({SourceFormat.PPTX}),
            parser_version="cosmos-pptx-ingestion-0.1.0",
        )

    def ingest(self, request: IngestionRequest) -> IngestionResult:
        content = self._load_verified_content(request)
        self._require_format(request.artifact, SourceFormat.PPTX)

        slides = _extract_pptx_slides(content)
        envelope = build_structured_text_envelope(
            {
                "format": "PPTX",
                "slides": list(slides),
            },
        )

        return self._build_result(
            request,
            envelope,
            normalized_format=NormalizedDocumentFormat.STRUCTURED_TEXT,
        )
