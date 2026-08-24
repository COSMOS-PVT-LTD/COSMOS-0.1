"""Real PDF → candidates → governed approval → evidence-backed answer."""

from __future__ import annotations

from knowledge.equations import EquationValidationState
from knowledge.foundation import KnowledgeFoundationService, PipelineEventKind
from knowledge.foundation.equation_approval import EquationReviewDecision
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.pdf.corpus import (
    ambiguous_reynolds_pdf_bytes,
    image_only_pdf_bytes,
    inconsistent_reynolds_pdf_bytes,
    mixed_reynolds_pdf_bytes,
    no_equation_pdf_bytes,
    reynolds_pdf_bytes,
)
from knowledge.pdf.models import ExtractionStatus
from knowledge.pdf.writer import write_extractable_pdf
from knowledge.source.integrity import sha256_bytes_digest


def _ingest(service: KnowledgeFoundationService, content: bytes, suffix: str):
    return service.ingest_real_pdf(
        content,
        source_id=f"SRC-COSMOS-{suffix}",
        document_id=f"DOC-COSMOS-{suffix}",
        title="COSMOS Reynolds qualification original",
        filename=f"{suffix}.pdf",
        reference_id=f"REF-COSMOS-{suffix}",
        author="COSMOS",
    )


def test_real_pdf_e2e_register_extract_approve_search_answer() -> None:
    service = KnowledgeFoundationService.with_seed_corpus()
    content = reynolds_pdf_bytes()
    digest = sha256_bytes_digest(content)
    result = _ingest(service, content, "RE-E2E")
    assert result.registered is not None
    assert result.registered.content_hash == digest
    assert result.status is ExtractionStatus.TEXT_AVAILABLE
    assert result.extraction is not None
    assert result.extraction.diagnostics.page_count == 1
    assert result.structure is not None
    assert result.structure.headings
    assert result.structure.paragraphs
    assert result.equation_candidates
    candidate = result.equation_candidates[0]
    assert candidate.raw_text == "Re = rho * V * D / mu"
    assert candidate.provenance.page == 1
    assert all(item.lifecycle is KnowledgeLifecycle.CANDIDATE for item in result.validated_equations)
    assert result.authoritative is False
    assert result.review_packages
    package = result.review_packages[0]
    assert package.excerpt == candidate.raw_text
    assert package.page_number == 1
    assert package.confidence > 0
    validated = result.validated_equations[0]
    assert validated.dimension_state is EquationValidationState.VALID
    assert validated.state is EquationValidationState.REVIEW_REQUIRED
    kinds = {event.kind for event in result.events}
    assert PipelineEventKind.SOURCE_REGISTERED in kinds
    assert PipelineEventKind.CANDIDATE_EXTRACTED in kinds
    assert PipelineEventKind.REVIEW_REQUIRED in kinds
    assert PipelineEventKind.APPROVED not in kinds

    approved = service.approve_real_equation(
        result,
        candidate.candidate_id,
        EquationReviewDecision.APPROVE,
        reference_id="REF-COSMOS-RE-E2E",
        title="Reynolds number",
    )
    assert approved.lifecycle is KnowledgeLifecycle.APPROVED
    assert service.graph_integrity_passed()

    search = service.search("Re = rho")
    assert search.hits
    assert any(hit.entity_id == candidate.candidate_id for hit in search.hits)
    assert search.provenance_ids
    answer = service.answer("Re = rho")
    assert answer.supporting_entities
    assert answer.source_references
    assert answer.validation_state
    assert answer.limitations
    assert answer.evidence or answer.supporting_entities


def test_negative_image_only_ocr_unavailable() -> None:
    service = KnowledgeFoundationService()
    result = _ingest(service, image_only_pdf_bytes(), "IMG")
    assert result.status is ExtractionStatus.EXTRACTION_UNAVAILABLE
    assert result.equation_candidates == ()
    assert result.recovered_text == ""
    assert any(event.kind is PipelineEventKind.EXTRACTION_UNAVAILABLE for event in result.events)


def test_negative_no_equation_not_guessed() -> None:
    service = KnowledgeFoundationService()
    result = _ingest(service, no_equation_pdf_bytes(), "NOEQ")
    assert result.status is ExtractionStatus.TEXT_AVAILABLE
    assert result.equation_candidates == ()
    assert result.review_packages == ()


def test_negative_dimensional_inconsistency() -> None:
    service = KnowledgeFoundationService()
    result = _ingest(service, inconsistent_reynolds_pdf_bytes(), "DIM")
    assert result.validated_equations
    assert result.validated_equations[0].state is EquationValidationState.VALIDATION_FAILURE
    try:
        service.approve_real_equation(
            result,
            result.equation_candidates[0].candidate_id,
            EquationReviewDecision.APPROVE,
            reference_id="REF-COSMOS-DIM",
            title="bad",
        )
        raise AssertionError("inconsistent equation must not approve")
    except ValueError:
        pass


def test_negative_ambiguous_variable() -> None:
    service = KnowledgeFoundationService()
    result = _ingest(service, ambiguous_reynolds_pdf_bytes(), "AMB")
    assert result.validated_equations
    assert result.validated_equations[0].state in {
        EquationValidationState.AMBIGUOUS,
        EquationValidationState.REVIEW_REQUIRED,
    }
    assert result.validated_equations[0].lifecycle is KnowledgeLifecycle.CANDIDATE


def test_negative_modified_source_hash_mismatch() -> None:
    service = KnowledgeFoundationService()
    first = reynolds_pdf_bytes()
    _ingest(service, first, "HASH")
    modified = write_extractable_pdf((("Chapter 1 changed", "Eq. 1 Re = rho * V * D / mu"),))
    result = service.ingest_real_pdf(
        modified,
        source_id="SRC-COSMOS-HASH",
        document_id="DOC-COSMOS-HASH-2",
        title="COSMOS Reynolds qualification original",
        filename="hash-modified.pdf",
        reference_id="REF-COSMOS-HASH",
    )
    assert result.status is ExtractionStatus.HASH_MISMATCH
    assert result.equation_candidates == ()


def test_negative_contradictory_sources() -> None:
    service = KnowledgeFoundationService()
    left = _ingest(service, reynolds_pdf_bytes(), "C1")
    right = _ingest(service, inconsistent_reynolds_pdf_bytes(), "C2")
    from knowledge.equations import CONTRADICTION_DETECTED, detect_equation_conflicts

    conflicts = detect_equation_conflicts(left.equation_candidates + right.equation_candidates)
    assert conflicts
    assert all(item.reason == CONTRADICTION_DETECTED for item in conflicts)


def test_mixed_pdf_keeps_native_text() -> None:
    service = KnowledgeFoundationService()
    result = _ingest(service, mixed_reynolds_pdf_bytes(), "MIX")
    assert result.status is ExtractionStatus.TEXT_AVAILABLE
    assert result.equation_candidates
    assert result.extraction is not None
    assert result.extraction.diagnostics.pages_with_text >= 1
    if result.extraction.method == "pypdf":
        assert result.extraction.diagnostics.page_count >= 1
    else:
        assert result.extraction.diagnostics.page_count == 2


def test_candidate_never_outranks_without_approval() -> None:
    service = KnowledgeFoundationService.with_seed_corpus()
    result = _ingest(service, reynolds_pdf_bytes(), "UNAPPROVED")
    assert result.authoritative is False
    search = service.search(result.equation_candidates[0].raw_text)
    if search.hits:
        unapproved = [hit for hit in search.hits if hit.entity_id == result.equation_candidates[0].candidate_id]
        assert unapproved == []
