"""Equation approval pipeline — candidate → normalize → review → approve."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.extraction.equation import CandidateEquationExtraction
from knowledge.models.dimension_check import DimensionCheckResult, DimensionExponents, check_dimensional_consistency
from knowledge.models.lifecycle import KnowledgeLifecycle

__all__ = (
    "EquationApprovalPipeline",
    "EquationReviewDecision",
    "NormalizedEquationCandidate",
)


class EquationReviewDecision(Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    RETURN_TO_CANDIDATE = "RETURN_TO_CANDIDATE"
    REQUEST_REVIEW = "REQUEST_REVIEW"


@dataclass(frozen=True, slots=True, kw_only=True)
class NormalizedEquationCandidate:
    extraction_id: str
    document_id: str
    raw_representation: str
    normalized_expression: str
    variable_symbols: tuple[str, ...]
    dimension_check: DimensionCheckResult | None
    lifecycle: KnowledgeLifecycle
    source_unknown: bool


class EquationApprovalPipeline:
    """Never auto-approves. Human review is mandatory."""

    def normalize(
        self,
        candidate: CandidateEquationExtraction,
        *,
        variable_exponents: dict[str, DimensionExponents] | None = None,
    ) -> NormalizedEquationCandidate:
        raw = candidate.raw_representation.strip()
        normalized = " ".join(raw.replace("×", "*").split())
        check = None
        if variable_exponents and "=" in normalized:
            check = check_dimensional_consistency(normalized, variable_exponents)
        anchor = candidate.provenance.anchor
        source_unknown = not (anchor.source_id or anchor.document_id)
        return NormalizedEquationCandidate(
            extraction_id=candidate.extraction_id,
            document_id=candidate.document_id,
            raw_representation=raw,
            normalized_expression=normalized,
            variable_symbols=candidate.variable_symbols,
            dimension_check=check,
            lifecycle=KnowledgeLifecycle.CANDIDATE,
            source_unknown=source_unknown,
        )

    def review(
        self,
        candidate: NormalizedEquationCandidate,
        decision: EquationReviewDecision,
        *,
        reviewer: str,
    ) -> NormalizedEquationCandidate:
        if not reviewer.strip():
            raise ValueError("reviewer is required.")
        if candidate.source_unknown:
            raise ValueError("Unknown-source equations cannot be approved.")
        if (
            decision is EquationReviewDecision.APPROVE
            and candidate.dimension_check is not None
            and not candidate.dimension_check.passed
        ):
            raise ValueError("Dimensionally inconsistent equations cannot be approved.")

        lifecycle = {
            EquationReviewDecision.APPROVE: KnowledgeLifecycle.APPROVED,
            EquationReviewDecision.REJECT: KnowledgeLifecycle.ARCHIVED,
            EquationReviewDecision.RETURN_TO_CANDIDATE: KnowledgeLifecycle.CANDIDATE,
            EquationReviewDecision.REQUEST_REVIEW: KnowledgeLifecycle.CANDIDATE,
        }[decision]
        return NormalizedEquationCandidate(
            extraction_id=candidate.extraction_id,
            document_id=candidate.document_id,
            raw_representation=candidate.raw_representation,
            normalized_expression=candidate.normalized_expression,
            variable_symbols=candidate.variable_symbols,
            dimension_check=candidate.dimension_check,
            lifecycle=lifecycle,
            source_unknown=candidate.source_unknown,
        )
