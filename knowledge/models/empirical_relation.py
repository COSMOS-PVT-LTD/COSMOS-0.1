"""Canonical EmpiricalRelation — sibling of Correlation, not a subtype."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.engineering_relation import EngineeringRelation, EngineeringRelationKind
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace, VersionRecord

__all__ = ("EmpiricalRelation",)


@dataclass(frozen=True, slots=True, kw_only=True)
class EmpiricalRelation:
    """Data-derived relation that is not a named heat-transfer correlation."""

    relation_id: str
    name: str
    equation: str
    variables: tuple[str, ...]
    domain: str
    data_basis: str
    provenance: ProvenanceTrace
    assumptions: tuple[str, ...] = ()
    applicability: str | None = None
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE
    version: VersionRecord | None = None
    validation_status: str = "UNREVIEWED"

    def __post_init__(self) -> None:
        if not self.relation_id.strip() or not self.name.strip():
            raise ValueError("relation_id and name are required.")
        if not self.equation.strip() or not self.data_basis.strip():
            raise ValueError("equation and data_basis are required.")

    def as_relation(self) -> EngineeringRelation:
        return EngineeringRelation(
            relation_id=self.relation_id,
            name=self.name,
            kind=EngineeringRelationKind.EMPIRICAL_RELATION,
            statement=self.equation,
            domain=self.domain,
            provenance=self.provenance,
            lifecycle=self.lifecycle,
            version=self.version,
            assumptions=self.assumptions,
            variable_ids=self.variables,
            applicability=self.applicability,
        )
