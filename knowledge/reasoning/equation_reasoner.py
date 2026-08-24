"""Equation reasoner facade over W10 provenance-aware reasoning."""

from __future__ import annotations

from knowledge.models.equation import Equation
from knowledge.models.lifecycle import KnowledgeLifecycle

__all__ = ("EquationReasoningResult", "reason_about_equation")

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class EquationReasoningResult:
    conclusion: str
    supporting_equation_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    validity_range: str | None
    confidence: float
    contradictions: tuple[str, ...]


def reason_about_equation(equation: Equation) -> EquationReasoningResult:
    approved = equation.status.value == "APPROVED"
    return EquationReasoningResult(
        conclusion=equation.expression,
        supporting_equation_ids=(equation.equation_id,),
        assumptions=(),
        validity_range=None,
        confidence=0.9 if approved else 0.3,
        contradictions=(),
    )
