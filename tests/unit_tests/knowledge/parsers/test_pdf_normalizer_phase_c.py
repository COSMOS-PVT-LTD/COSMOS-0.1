"""Additional pdf_normalizer coverage for KG-BLOCK-013 Phase C (DEV-010)."""

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


def test_normalize_pdf_outline_skips_non_heading_lines() -> None:
    """Non-heading content must not create sections."""

    normalization_input = PdfNormalizationInput(
        document_id="DOC-001",
        source_id="SRC-001",
        artifact_id="ART-001",
        outline_text="Plain paragraph without heading\n# Real Section",
        parser_version="0.1.0",
    )

    document = normalize_pdf_outline(
        normalization_input,
        _sample_ingestion_result(),
    )

    assert len(document.sections) == 1
    assert document.sections[0].title == "Real Section"


def test_normalize_pdf_outline_rejects_non_positive_page_marker() -> None:
    """Page markers must reject zero and negative values."""

    normalization_input = PdfNormalizationInput(
        document_id="DOC-001",
        source_id="SRC-001",
        artifact_id="ART-001",
        outline_text="<!-- page: 0 -->\n# Section",
        parser_version="0.1.0",
    )

    with pytest.raises(ParserValidationError):
        normalize_pdf_outline(
            normalization_input,
            _sample_ingestion_result(),
        )
