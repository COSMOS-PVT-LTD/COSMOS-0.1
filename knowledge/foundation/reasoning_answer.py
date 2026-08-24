"""Provenance-aware reasoning result for engineering answers."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.lifecycle import KnowledgeLifecycle

__all__ = ("EngineeringAnswer", "assemble_engineering_answer")


@dataclass(frozen=True, slots=True, kw_only=True)
class EngineeringAnswer:
    conclusion: str
    supporting_equation_ids: tuple[str, ...]
    supporting_document_ids: tuple[str, ...]
    supporting_entities: tuple[str, ...]
    source_references: tuple[str, ...]
    assumptions: tuple[str, ...]
    validity_range: str | None
    engineering_domain: str
    evidence: tuple[str, ...]
    contradictions: tuple[str, ...]
    confidence: float
    lifecycle: KnowledgeLifecycle
    validation_state: str
    limitations: str


def assemble_engineering_answer(
    *,
    conclusion: str,
    equation_ids: tuple[str, ...] = (),
    document_ids: tuple[str, ...] = (),
    supporting_entities: tuple[str, ...] = (),
    source_references: tuple[str, ...] = (),
    assumptions: tuple[str, ...] = (),
    validity_range: str | None = None,
    domain: str,
    evidence: tuple[str, ...] = (),
    contradictions: tuple[str, ...] = (),
    approved: bool,
    limitations: str | None = None,
) -> EngineeringAnswer:
    confidence = 0.85 if approved and not contradictions else 0.35
    if contradictions:
        confidence = min(confidence, 0.25)
    return EngineeringAnswer(
        conclusion=conclusion,
        supporting_equation_ids=equation_ids,
        supporting_document_ids=document_ids,
        supporting_entities=supporting_entities or equation_ids,
        source_references=source_references or document_ids,
        assumptions=assumptions,
        validity_range=validity_range,
        engineering_domain=domain,
        evidence=evidence,
        contradictions=contradictions,
        confidence=confidence,
        lifecycle=KnowledgeLifecycle.APPROVED if approved else KnowledgeLifecycle.CANDIDATE,
        validation_state="APPROVED" if approved else "CANDIDATE",
        limitations=limitations
        or (
            "Contradicting sources require engineer review."
            if contradictions
            else "Valid only within cited applicability and approval envelope."
        ),
    )
