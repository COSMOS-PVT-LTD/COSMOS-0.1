"""End-to-end: markdown → parse → extract → review → search → provenance."""

from __future__ import annotations

from pathlib import Path

from knowledge.foundation import KnowledgeFoundationService
from knowledge.foundation.equation_approval import EquationReviewDecision
from knowledge.foundation.variable_catalog import SI_EXPONENTS
from knowledge.models.lifecycle import KnowledgeLifecycle

_GOLDEN = Path(__file__).resolve().parents[3] / "fixtures" / "knowledge" / "golden" / "regenerative_cooling.md"


def test_golden_markdown_to_approved_search() -> None:
    service = KnowledgeFoundationService.with_seed_corpus()
    content = _GOLDEN.read_text(encoding="utf-8")
    draft = service.ingest_markdown(
        content,
        source_id="SRC-GOLDEN-8087",
        artifact_id="ART-GOLDEN-8087",
        reference_id="REF-NASA-SP-8087",
    )
    assert draft.equation_candidates
    assert draft.correlation_candidates
    assert all(item.lifecycle is KnowledgeLifecycle.CANDIDATE for item in draft.normalized_equations)

    reynolds = next(
        item
        for item in draft.normalized_equations
        if "Re" in item.normalized_expression and "rho" in item.normalized_expression
    )
    checked = service.approval.normalize(
        next(item for item in draft.equation_candidates if item.extraction_id == reynolds.extraction_id),
        variable_exponents={symbol: SI_EXPONENTS[symbol] for symbol in ("Re", "rho", "V", "D", "mu")},
    )
    approved = service.review_equation(checked, EquationReviewDecision.APPROVE)
    assert approved.lifecycle is KnowledgeLifecycle.APPROVED
    assert approved.dimension_check is not None
    assert approved.dimension_check.passed is True

    result = service.search("Bartz")
    assert result.hits
    assert result.provenance_ids
    answer = service.answer("Bartz regenerative cooling")
    assert answer.lifecycle is KnowledgeLifecycle.APPROVED
    assert answer.confidence >= 0.8
    assert answer.supporting_document_ids
