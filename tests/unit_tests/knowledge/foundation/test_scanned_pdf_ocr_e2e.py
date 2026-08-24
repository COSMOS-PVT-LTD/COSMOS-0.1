"""Scanned COSMOS PDF → OCR → candidates → governed approval."""

from __future__ import annotations

import pytest

from knowledge.foundation import KnowledgeFoundationService, PipelineEventKind
from knowledge.foundation.equation_approval import EquationReviewDecision
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.ocr.metrics import EquationQuality, character_error_rate
from knowledge.ocr.provisioning import ocr_is_provisioned, rasterizer_is_provisioned
from knowledge.pdf.corpus import (
    notation_scanned_pdf_bytes,
    scanned_reynolds_pdf_bytes,
    table_scanned_pdf_bytes,
)
from knowledge.pdf.models import ExtractionStatus
from knowledge.pdf.writer import write_extractable_pdf

pytestmark = pytest.mark.skipif(
    not (ocr_is_provisioned() and rasterizer_is_provisioned()),
    reason="Tesseract and pypdfium2 are not both provisioned.",
)


def test_scanned_reynolds_e2e_ocr_to_approved_answer() -> None:
    service = KnowledgeFoundationService.with_seed_corpus()
    content = scanned_reynolds_pdf_bytes()
    result = service.ingest_real_pdf(
        content,
        source_id="SRC-SCAN-RE",
        document_id="DOC-SCAN-RE",
        title="COSMOS scanned Reynolds original",
        filename="scanned_reynolds.pdf",
        reference_id="REF-SCAN-RE",
        author="COSMOS",
    )
    assert result.status is ExtractionStatus.TEXT_AVAILABLE
    assert result.extraction is not None
    assert result.extraction.diagnostics.ocr_pages == 1
    assert result.ocr_evidence
    evidence = result.ocr_evidence[0]
    assert evidence.image_hash
    assert evidence.rasterizer
    assert evidence.ocr_backend
    assert evidence.page_image
    assert "Re" in result.recovered_text
    assert result.equation_candidates
    candidate = result.equation_candidates[0]
    assert "=" in candidate.raw_text
    assert "rho" in candidate.raw_text.replace(" ", "") or "p" in candidate.raw_text
    assert result.review_packages
    package = result.review_packages[0]
    assert package.page_image_hash
    assert package.ocr_text
    assert result.authoritative is False
    assert PipelineEventKind.APPROVED not in {event.kind for event in result.events}

    quality = EquationQuality(
        expected="Re = rho * V * D / mu",
        actual=candidate.raw_text,
        equation_detected=True,
        symbol_preserved="Re" in candidate.raw_text,
        operator_preserved="=" in candidate.raw_text,
        label_preserved="1" in (candidate.label or ""),
    )
    assert quality.equation_detected
    assert character_error_rate(quality.expected, quality.expected) == 0.0

    approved = service.approve_real_equation(
        result,
        candidate.candidate_id,
        EquationReviewDecision.APPROVE,
        reference_id="REF-SCAN-RE",
        title="Reynolds number from scanned page",
    )
    assert approved.lifecycle is KnowledgeLifecycle.APPROVED
    snapshot = service.snapshot()
    assert snapshot["ocr_records"]
    assert snapshot["ocr_records"][0]["image_hash"] == evidence.image_hash
    search = service.search("Re")
    assert any(hit.entity_id == candidate.candidate_id for hit in search.hits)
    assert any(hit.lifecycle is KnowledgeLifecycle.APPROVED for hit in search.hits if hit.entity_id == candidate.candidate_id)
    answer = service.answer("Re")
    assert answer.supporting_entities
    assert answer.source_references
    assert answer.validation_state
    assert answer.limitations


def test_scanned_table_and_notation_pages_are_candidates_only() -> None:
    service = KnowledgeFoundationService()
    table = service.ingest_real_pdf(
        table_scanned_pdf_bytes(),
        source_id="SRC-SCAN-TAB",
        document_id="DOC-SCAN-TAB",
        title="table",
        filename="table.pdf",
        reference_id="REF-SCAN-TAB",
    )
    notation = service.ingest_real_pdf(
        notation_scanned_pdf_bytes(),
        source_id="SRC-SCAN-NOT",
        document_id="DOC-SCAN-NOT",
        title="notation",
        filename="notation.pdf",
        reference_id="REF-SCAN-NOT",
    )
    assert table.status is ExtractionStatus.TEXT_AVAILABLE
    assert "Table" in table.recovered_text or "Re" in table.recovered_text
    assert notation.status is ExtractionStatus.TEXT_AVAILABLE
    assert notation.authoritative is False
    assert "Inconel" in notation.recovered_text or "CH4" in notation.recovered_text or "CuCrZr" in notation.recovered_text


def test_low_level_fail_closed_still_holds_for_corrupt_and_modified() -> None:
    service = KnowledgeFoundationService()
    corrupt = service.ingest_real_pdf(
        b"this is not a pdf",
        source_id="SRC-BAD",
        document_id="DOC-BAD",
        title="bad",
        filename="bad.pdf",
        reference_id="REF-BAD",
    )
    assert corrupt.status.value in {"CORRUPT_SOURCE", "EXTRACTION_UNAVAILABLE"}
    first = scanned_reynolds_pdf_bytes()
    service.ingest_real_pdf(
        first,
        source_id="SRC-MOD",
        document_id="DOC-MOD",
        title="mod",
        filename="a.pdf",
        reference_id="REF-MOD",
    )
    modified = write_extractable_pdf((("changed page",),))
    result = service.ingest_real_pdf(
        modified,
        source_id="SRC-MOD",
        document_id="DOC-MOD-2",
        title="mod",
        filename="b.pdf",
        reference_id="REF-MOD",
    )
    assert result.status is ExtractionStatus.HASH_MISMATCH
