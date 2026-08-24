"""Equation approval never auto-approves and rejects unknown sources."""

from __future__ import annotations

import pytest

from knowledge.extraction.equation import CandidateEquationExtraction, ExtractionConfidence
from knowledge.foundation.equation_approval import EquationApprovalPipeline, EquationReviewDecision
from knowledge.graph.contracts import ProvenanceReference
from knowledge.graph.lifecycle import GraphLifecycleState
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.models.dimension_check import DimensionExponents
from knowledge.models.lifecycle import KnowledgeLifecycle


def _candidate(*, source_id: str | None = "SRC-1", document_id: str | None = "DOC-1") -> CandidateEquationExtraction:
    return CandidateEquationExtraction(
        extraction_id="EXT-RE-1",
        document_id="DOC-1",
        raw_representation="Re = rho*V*D/mu",
        provenance=SourceProvenanceRecord(
            anchor=ProvenanceReference(
                source_id=source_id,
                document_id=document_id,
                location_anchor=None if source_id or document_id else "orphan",
            )
            if source_id or document_id
            else ProvenanceReference(location_anchor="orphan"),
        ),
        confidence_band=ExtractionConfidence.HIGH,
        confidence_score=0.9,
        lifecycle_state=GraphLifecycleState.EXTRACTED,
        variable_symbols=("Re", "rho", "V", "D", "mu"),
    )


def test_normalize_stays_candidate() -> None:
    pipeline = EquationApprovalPipeline()
    normalized = pipeline.normalize(_candidate())
    assert normalized.lifecycle is KnowledgeLifecycle.CANDIDATE
    assert normalized.source_unknown is False


def test_unknown_source_cannot_be_approved() -> None:
    pipeline = EquationApprovalPipeline()
    normalized = pipeline.normalize(_candidate(source_id=None, document_id=None))
    assert normalized.source_unknown is True
    with pytest.raises(ValueError, match="Unknown-source"):
        pipeline.review(normalized, EquationReviewDecision.APPROVE, reviewer="alice")


def test_human_review_required_for_approval() -> None:
    pipeline = EquationApprovalPipeline()
    exponents: dict[str, DimensionExponents] = {
        "Re": (0, 0, 0, 0, 0, 0, 0),
        "rho": (-3, 1, 0, 0, 0, 0, 0),
        "V": (1, 0, -1, 0, 0, 0, 0),
        "D": (1, 0, 0, 0, 0, 0, 0),
        "mu": (-1, 1, -1, 0, 0, 0, 0),
    }
    normalized = pipeline.normalize(_candidate(), variable_exponents=exponents)
    assert normalized.dimension_check is not None
    assert normalized.dimension_check.passed is True
    approved = pipeline.review(normalized, EquationReviewDecision.APPROVE, reviewer="alice")
    assert approved.lifecycle is KnowledgeLifecycle.APPROVED
