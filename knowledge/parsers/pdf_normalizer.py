"""
COSMOS Knowledge Foundation

Module:
    knowledge.parsers.pdf_normalizer

Purpose:
    PDF normalization contracts operating on pre-extracted text outlines.
"""

from __future__ import annotations

import re

from knowledge.graph.provenance import ExtractionProvenance
from knowledge.ingestion.models import IngestionResult
from knowledge.parsers.exceptions import ParserValidationError
from knowledge.parsers.models import (
    DocumentSection,
    NormalizedParsedDocument,
    PageAnchor,
)

__all__ = (
    "PdfNormalizationInput",
    "normalize_pdf_outline",
)

_HEADING_PATTERN = re.compile(r"^(?P<level>#{1,6})\s+(?P<title>.+)$")


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ParserValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise ParserValidationError(f"{field_name} must not be blank.")

    return cleaned


class PdfNormalizationInput:
    """
    Deterministic PDF normalization input.

    Accepts pre-extracted markdown-like outline text rather than reading PDF
    files directly.
    """

    def __init__(
        self,
        *,
        document_id: str,
        source_id: str,
        artifact_id: str,
        outline_text: str,
        parser_version: str,
    ) -> None:
        self.document_id = _validate_non_empty_string(
            "document_id",
            document_id,
        )
        self.source_id = _validate_non_empty_string("source_id", source_id)
        self.artifact_id = _validate_non_empty_string(
            "artifact_id",
            artifact_id,
        )
        self.outline_text = outline_text
        self.parser_version = _validate_non_empty_string(
            "parser_version",
            parser_version,
        )

def normalize_pdf_outline(
    normalization_input: PdfNormalizationInput,
    ingestion_result: IngestionResult,
) -> NormalizedParsedDocument:
    """
    Normalize a PDF outline into structured sections with page anchors.

    The function is deterministic for identical outline text and metadata.
    """

    if not isinstance(normalization_input, PdfNormalizationInput):
        raise ParserValidationError(
            "normalization_input must be a PdfNormalizationInput instance."
        )

    if not isinstance(ingestion_result, IngestionResult):
        raise ParserValidationError(
            "ingestion_result must be an IngestionResult instance."
        )

    sections: list[DocumentSection] = []
    current_page = 1

    for line_number, raw_line in enumerate(
        normalization_input.outline_text.splitlines(),
        start=1,
    ):
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("<!-- page:"):
            page_token = line.removeprefix("<!-- page:").removesuffix("-->").strip()

            try:
                current_page = int(page_token)
            except ValueError as exc:
                raise ParserValidationError(
                    "PDF page marker must contain a positive integer."
                ) from exc

            if current_page <= 0:
                raise ParserValidationError(
                    "PDF page marker must contain a positive integer."
                )

            continue

        match = _HEADING_PATTERN.match(line)

        if match is None:
            continue

        level = len(match.group("level"))
        title = match.group("title").strip()
        section_id = f"sec-{line_number:04d}"

        sections.append(
            DocumentSection(
                section_id=section_id,
                title=title,
                level=level,
                page_anchor=PageAnchor(
                    page_number=current_page,
                    section_id=section_id,
                ),
            )
        )

    extraction = ExtractionProvenance(
        extractor_tool="cosmos-pdf-normalizer",
        extractor_version=normalization_input.parser_version,
    )

    return NormalizedParsedDocument(
        document_id=normalization_input.document_id,
        source_id=normalization_input.source_id,
        artifact_id=normalization_input.artifact_id,
        parser_version=normalization_input.parser_version,
        sections=tuple(sections),
        extraction=extraction,
    )
