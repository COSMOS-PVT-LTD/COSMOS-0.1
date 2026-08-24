"""Canonical PhysicalLaw model."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.engineering_relation import EngineeringRelation, EngineeringRelationKind
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace, VersionRecord

__all__ = ("PhysicalLaw",)


@dataclass(frozen=True, slots=True, kw_only=True)
class PhysicalLaw:
    """First-principles physical law with formulation and assumptions."""

    law_id: str
    name: str
    description: str
    mathematical_formulation: str
    variables: tuple[str, ...]
    units: tuple[str, ...]
    assumptions: tuple[str, ...]
    domain: str
    applicability: str
    provenance: ProvenanceTrace
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE
    version: VersionRecord | None = None
    validation_status: str = "UNREVIEWED"

    def __post_init__(self) -> None:
        if not self.law_id.strip() or not self.name.strip():
            raise ValueError("law_id and name are required.")
        if not self.mathematical_formulation.strip():
            raise ValueError("mathematical_formulation is required.")
        if not isinstance(self.provenance, ProvenanceTrace):
            raise ValueError("provenance is required.")

    def as_relation(self) -> EngineeringRelation:
        return EngineeringRelation(
            relation_id=self.law_id,
            name=self.name,
            kind=EngineeringRelationKind.PHYSICAL_LAW,
            statement=self.mathematical_formulation,
            domain=self.domain,
            provenance=self.provenance,
            lifecycle=self.lifecycle,
            version=self.version,
            assumptions=self.assumptions,
            variable_ids=self.variables,
            applicability=self.applicability,
        )
