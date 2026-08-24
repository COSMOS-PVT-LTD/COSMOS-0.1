"""Canonical DesignRule — knowledge to design decision."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.engineering_relation import EngineeringRelation, EngineeringRelationKind
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace, VersionRecord

__all__ = ("DesignRule",)


@dataclass(frozen=True, slots=True, kw_only=True)
class DesignRule:
    """Engineering constraint expressed as a statement or inequality."""

    rule_id: str
    statement: str
    formula: str
    parameters: tuple[str, ...]
    applicability: str
    authority: str
    severity: str
    provenance: ProvenanceTrace
    domain: str = "STRUCTURES"
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE
    version: VersionRecord | None = None
    approval: str | None = None
    validation_status: str = "UNREVIEWED"

    def __post_init__(self) -> None:
        if not self.rule_id.strip() or not self.statement.strip():
            raise ValueError("rule_id and statement are required.")
        if not self.formula.strip():
            raise ValueError("formula is required.")
        if self.lifecycle is KnowledgeLifecycle.APPROVED and not self.approval:
            raise ValueError("APPROVED design rules require approval.")

    def as_relation(self) -> EngineeringRelation:
        return EngineeringRelation(
            relation_id=self.rule_id,
            name=self.statement,
            kind=EngineeringRelationKind.DESIGN_RULE,
            statement=self.formula,
            domain=self.domain,
            provenance=self.provenance,
            lifecycle=self.lifecycle,
            version=self.version,
            applicability=self.applicability,
        )
