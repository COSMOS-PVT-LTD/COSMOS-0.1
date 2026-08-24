"""Engineering relation hierarchy — PhysicalLaw / Correlation / EmpiricalRelation / DesignRule."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.models.lifecycle import (
    KnowledgeLifecycle,
    ProvenanceTrace,
    UncertaintyRecord,
    VerificationRecord,
    VersionRecord,
)

__all__ = (
    "EngineeringRelation",
    "EngineeringRelationKind",
)


class EngineeringRelationKind(Enum):
    """Semantic kind of an engineering relation."""

    PHYSICAL_LAW = "PHYSICAL_LAW"
    CORRELATION = "CORRELATION"
    EMPIRICAL_RELATION = "EMPIRICAL_RELATION"
    DESIGN_RULE = "DESIGN_RULE"


def _require_text(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-blank string.")
    return value.strip()


@dataclass(frozen=True, slots=True, kw_only=True)
class EngineeringRelation:
    """Shared contract for law / correlation / empirical / design-rule entities."""

    relation_id: str
    name: str
    kind: EngineeringRelationKind
    statement: str
    domain: str
    provenance: ProvenanceTrace
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE
    version: VersionRecord | None = None
    verification: VerificationRecord | None = None
    uncertainty: UncertaintyRecord | None = None
    assumptions: tuple[str, ...] = ()
    variable_ids: tuple[str, ...] = ()
    applicability: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "relation_id", _require_text("relation_id", self.relation_id))
        object.__setattr__(self, "name", _require_text("name", self.name))
        object.__setattr__(self, "statement", _require_text("statement", self.statement))
        object.__setattr__(self, "domain", _require_text("domain", self.domain))
        if not isinstance(self.kind, EngineeringRelationKind):
            raise ValueError("kind must be an EngineeringRelationKind.")
        if not isinstance(self.provenance, ProvenanceTrace):
            raise ValueError("provenance is required.")
        if self.lifecycle is KnowledgeLifecycle.APPROVED and self.verification is None:
            raise ValueError("APPROVED relations require a verification record.")

    def is_production_usable(self) -> bool:
        return self.lifecycle is KnowledgeLifecycle.APPROVED
