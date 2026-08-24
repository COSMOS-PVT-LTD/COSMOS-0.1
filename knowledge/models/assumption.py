"""Canonical Assumption model — equations without assumptions are unsafe."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace

__all__ = ("Assumption",)


@dataclass(frozen=True, slots=True, kw_only=True)
class Assumption:
    """Explicit engineering assumption bound to entities that depend on it."""

    assumption_id: str
    statement: str
    category: str
    affected_entity_ids: tuple[str, ...]
    provenance: ProvenanceTrace
    justification: str
    applicability: str
    confidence: float
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE
    created_by: str = "unknown"
    approved_by: str | None = None
    version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not self.assumption_id.strip() or not self.statement.strip():
            raise ValueError("assumption_id and statement are required.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0.")
        if self.lifecycle is KnowledgeLifecycle.APPROVED and not self.approved_by:
            raise ValueError("APPROVED assumptions require approved_by.")
