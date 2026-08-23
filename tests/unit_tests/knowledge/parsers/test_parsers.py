"""Unit tests for knowledge.parsers contracts."""

from __future__ import annotations

import pytest

from knowledge.ingestion import (
    IngestionArtifactRef,
    IngestionRequest,
    IngestionResult,
    NormalizedDocumentFormat,
    SourceFormat,
)
from knowledge.parsers import (
    DocumentSection,
    NormalizedParsedDocument,
    PageAnchor,
    ParserValidationError,
    PdfNormalizationInput,
    normalize_pdf_outline,
)

_VALID_SHA256 = "a" * 64


def _sample_ingestion_result() -> IngestionResult:
    artifact = IngestionArtifactRef(
        source_id="SRC-001",
        artifact_id="ART-001",
        source_format=SourceFormat.PDF,
    )

    return IngestionResult(
        request=IngestionRequest(
            artifact=artifact,
            adapter_name="pdf-adapter",
            adapter_version="0.1.0",
        ),
        normalized_format=NormalizedDocumentFormat.MARKDOWN,
        normalized_content_hash=_VALID_SHA256,
        parser_version="0.1.0",
        document_id="DOC-001",
    )


def test_normalized_parsed_document_rejects_duplicate_sections() -> None:
    """Parsed documents must reject duplicate section identifiers."""

    section = DocumentSection(section_id="sec-001", title="Intro")

    with pytest.raises(ParserValidationError):
        NormalizedParsedDocument(
            document_id="DOC-001",
            source_id="SRC-001",
            artifact_id="ART-001",
            parser_version="0.1.0",
            sections=(section, section),
        )


def test_normalize_pdf_outline_is_deterministic() -> None:
    """PDF normalization must preserve sections and page anchors."""

    outline = "\n".join(
        [
            "<!-- page: 1 -->",
            "# Introduction",
            "<!-- page: 3 -->",
            "## Chamber Pressure",
        ]
    )

    normalization_input = PdfNormalizationInput(
        document_id="DOC-001",
        source_id="SRC-001",
        artifact_id="ART-001",
        outline_text=outline,
        parser_version="0.1.0",
    )

    first = normalize_pdf_outline(
        normalization_input,
        _sample_ingestion_result(),
    )
    second = normalize_pdf_outline(
        normalization_input,
        _sample_ingestion_result(),
    )

    assert first == second
    assert len(first.sections) == 2
    assert first.sections[0].page_anchor == PageAnchor(
        page_number=1,
        section_id=first.sections[0].section_id,
    )
    assert first.sections[1].page_anchor == PageAnchor(
        page_number=3,
        section_id=first.sections[1].section_id,
    )


def test_normalize_pdf_outline_rejects_invalid_page_marker() -> None:
    """Invalid page markers must be rejected."""

    normalization_input = PdfNormalizationInput(
        document_id="DOC-001",
        source_id="SRC-001",
        artifact_id="ART-001",
        outline_text="<!-- page: zero -->",
        parser_version="0.1.0",
    )

    with pytest.raises(ParserValidationError):
        normalize_pdf_outline(
            normalization_input,
            _sample_ingestion_result(),
        )
