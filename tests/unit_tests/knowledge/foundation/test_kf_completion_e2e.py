"""Knowledge Foundation completion E2E: native, scanned, reconstruction, SQLite."""

from __future__ import annotations

from pathlib import Path

import pytest

from knowledge.equations.reconstruction import ReconstructionState
from knowledge.foundation import KnowledgeFoundationService, PipelineEventKind
from knowledge.foundation.equation_approval import EquationReviewDecision
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.ocr.provisioning import ocr_is_provisioned, rasterizer_is_provisioned
from knowledge.pdf.corpus import (
    complex_equation_pdf_bytes,
    greek_symbol_pdf_bytes,
    reynolds_pdf_bytes,
    scanned_reynolds_pdf_bytes,
)
from knowledge.pdf.models import ExtractionStatus


def test_native_pdf_reconstruction_and_sqlite_trace(tmp_path: Path) -> None:
    service = KnowledgeFoundationService.with_seed_corpus()
    database = service.attach_database(tmp_path / "kf.sqlite")
    result = service.ingest_real_pdf(
        reynolds_pdf_bytes(),
        source_id="SRC-KF-NATIVE",
        document_id="DOC-KF-NATIVE",
        title="COSMOS Reynolds",
        filename="reynolds.pdf",
        reference_id="REF-KF-NATIVE",
        author="COSMOS",
    )
    assert result.status is ExtractionStatus.TEXT_AVAILABLE
    assert result.equation_candidates
    assert result.reconstructions
    reconstructed = result.reconstructions[0]
    assert reconstructed.source_representation == "Re = rho * V * D / mu"
    assert reconstructed.latex
    assert reconstructed.state in {ReconstructionState.RECONSTRUCTED, ReconstructionState.REVIEW_REQUIRED}
    package = result.review_packages[0]
    assert package.normalized_representation
    assert package.latex
    service.persist_to_database(result)
    approved = service.approve_real_equation(
        result,
        result.equation_candidates[0].candidate_id,
        EquationReviewDecision.APPROVE,
        reference_id="REF-KF-NATIVE",
        title="Reynolds number",
    )
    assert approved.lifecycle is KnowledgeLifecycle.APPROVED
    chain = database.trace_equation(result.equation_candidates[0].candidate_id)
    assert chain.content_hash == result.registered.content_hash
    assert chain.approval_decision == "APPROVE"
    search = service.search("Re")
    assert search.hits
    answer = service.answer("Re")
    assert answer.supporting_entities
    assert answer.source_references
    assert PipelineEventKind.APPROVED not in {event.kind for event in result.events}


def test_complex_and_greek_pages_keep_source_symbols() -> None:
    service = KnowledgeFoundationService()
    complex_result = service.ingest_real_pdf(
        complex_equation_pdf_bytes(),
        source_id="SRC-COMPLEX",
        document_id="DOC-COMPLEX",
        title="complex",
        filename="complex.pdf",
        reference_id="REF-COMPLEX",
    )
    assert any("(rho * V * D) / mu" in item.raw_text for item in complex_result.equation_candidates)
    greek = service.ingest_real_pdf(
        greek_symbol_pdf_bytes(),
        source_id="SRC-GREEK",
        document_id="DOC-GREEK",
        title="greek",
        filename="greek.pdf",
        reference_id="REF-GREEK",
    )
    assert "rho" in greek.recovered_text
    assert "μ" not in greek.equation_candidates[0].raw_text


def test_scanned_path_still_requires_review() -> None:
    if not (ocr_is_provisioned() and rasterizer_is_provisioned()):
        pytest.skip("Tesseract and pypdfium2 are not both provisioned.")
    service = KnowledgeFoundationService()
    result = service.ingest_real_pdf(
        scanned_reynolds_pdf_bytes(),
        source_id="SRC-SCAN-KF",
        document_id="DOC-SCAN-KF",
        title="scanned",
        filename="scanned.pdf",
        reference_id="REF-SCAN-KF",
    )
    assert result.status is ExtractionStatus.TEXT_AVAILABLE
    assert result.ocr_jobs
    assert result.math_ocr_results
    assert result.authoritative is False
    assert PipelineEventKind.APPROVED not in {event.kind for event in result.events}
