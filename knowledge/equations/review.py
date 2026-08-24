"""Human review package for equation candidates. Never auto-approves."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from knowledge.equations.models import EquationValidationState, ValidatedEquationCandidate
from knowledge.models.lifecycle import KnowledgeLifecycle

if TYPE_CHECKING:
    from knowledge.foundation.equation_approval import (
        EquationReviewDecision,
        NormalizedEquationCandidate,
    )

__all__ = ("EquationReviewPackage", "build_review_package", "review_validated_equation")


@dataclass(frozen=True, slots=True, kw_only=True)
class EquationReviewPackage:
    candidate_id: str
    excerpt: str
    page_number: int | None
    source_id: str
    document_id: str
    validation_state: str
    confidence: float
    reasons: tuple[str, ...]
    raw_text: str
    variables: tuple[str, ...]
    validated: ValidatedEquationCandidate
    page_image_hash: str | None = None
    ocr_text: str | None = None
    ocr_confidence: float | None = None
    ocr_backend: str | None = None
    warnings: tuple[str, ...] = ()
    normalized_representation: str | None = None
    math_ocr_text: str | None = None
    latex: str | None = None
    limitations: tuple[str, ...] = ()


def build_review_package(validated: ValidatedEquationCandidate) -> EquationReviewPackage:
    candidate = validated.candidate
    return EquationReviewPackage(
        candidate_id=candidate.candidate_id,
        excerpt=candidate.raw_text,
        page_number=candidate.page_number,
        source_id=candidate.source_id,
        document_id=candidate.document_id,
        validation_state=validated.state.value,
        confidence=candidate.confidence,
        reasons=validated.reasons,
        raw_text=candidate.raw_text,
        variables=tuple(item.symbol for item in candidate.variables),
        validated=validated,
        page_image_hash=None,
        ocr_text=candidate.ocr_text,
        ocr_confidence=None,
        ocr_backend=None,
        warnings=(),
        normalized_representation=None,
        math_ocr_text=None,
        latex=candidate.latex,
        limitations=(),
    )


def review_validated_equation(
    validated: ValidatedEquationCandidate,
    decision: EquationReviewDecision,
    *,
    reviewer: str,
) -> NormalizedEquationCandidate:
    from knowledge.foundation.equation_approval import (
        EquationApprovalPipeline,
        EquationReviewDecision as ReviewDecision,
    )

    blocked = {
        EquationValidationState.NON_AUTHORITATIVE,
        EquationValidationState.INVALID,
        EquationValidationState.VALIDATION_FAILURE,
        EquationValidationState.EXTRACTION_UNAVAILABLE,
    }
    if validated.state in blocked and decision is ReviewDecision.APPROVE:
        raise ValueError(f"Cannot approve equation in state {validated.state.value}.")
    pipeline = EquationApprovalPipeline()
    normalized = pipeline.normalize(validated.candidate.to_extraction())
    if decision is ReviewDecision.APPROVE and normalized.source_unknown:
        raise ValueError("Unknown-source equations cannot be approved.")
    reviewed = pipeline.review(normalized, decision, reviewer=reviewer)
    if reviewed.lifecycle is KnowledgeLifecycle.APPROVED and not reviewer.strip():
        raise ValueError("Approval requires a reviewer.")
    return reviewed
