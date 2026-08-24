"""Expanded engineering relationship vocabulary (additive — does not modify frozen ontology models)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = (
    "ENGINEERING_RELATIONSHIP_TERMS",
    "EngineeringRelationship",
    "RelationshipSpec",
    "relationship_spec",
)


class EngineeringRelationship(Enum):
    """Standardized engineering graph relationships."""

    IS_A = "is_a"
    PART_OF = "part_of"
    DEPENDS_ON = "depends_on"
    DERIVED_FROM = "derived_from"
    USES = "uses"
    VALID_FOR = "valid_for"
    INVALID_FOR = "invalid_for"
    MEASURED_BY = "measured_by"
    VALIDATED_BY = "validated_by"
    SUPERSEDES = "supersedes"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    REQUIRES = "requires"
    CAUSES = "causes"
    MITIGATES = "mitigates"


ENGINEERING_RELATIONSHIP_TERMS: frozenset[str] = frozenset(
    item.value for item in EngineeringRelationship
)


@dataclass(frozen=True, slots=True, kw_only=True)
class RelationshipSpec:
    relationship: EngineeringRelationship
    definition: str
    source_kinds: frozenset[str]
    target_kinds: frozenset[str]
    cardinality: str
    acyclic: bool


_SPECS: dict[EngineeringRelationship, RelationshipSpec] = {
    EngineeringRelationship.IS_A: RelationshipSpec(
        relationship=EngineeringRelationship.IS_A,
        definition="Taxonomic specialization.",
        source_kinds=frozenset({"entity"}),
        target_kinds=frozenset({"entity", "class"}),
        cardinality="many-to-one",
        acyclic=True,
    ),
    EngineeringRelationship.PART_OF: RelationshipSpec(
        relationship=EngineeringRelationship.PART_OF,
        definition="Composition of an engineering assembly.",
        source_kinds=frozenset({"component", "subsystem"}),
        target_kinds=frozenset({"component", "subsystem"}),
        cardinality="many-to-one",
        acyclic=True,
    ),
    EngineeringRelationship.DEPENDS_ON: RelationshipSpec(
        relationship=EngineeringRelationship.DEPENDS_ON,
        definition="Hard functional dependency.",
        source_kinds=frozenset({"entity"}),
        target_kinds=frozenset({"entity"}),
        cardinality="many-to-many",
        acyclic=True,
    ),
    EngineeringRelationship.DERIVED_FROM: RelationshipSpec(
        relationship=EngineeringRelationship.DERIVED_FROM,
        definition="Derived from a source document or parent relation.",
        source_kinds=frozenset({"entity"}),
        target_kinds=frozenset({"document", "reference", "entity"}),
        cardinality="many-to-many",
        acyclic=True,
    ),
    EngineeringRelationship.USES: RelationshipSpec(
        relationship=EngineeringRelationship.USES,
        definition="Uses a variable, material, or supporting relation.",
        source_kinds=frozenset({"equation", "correlation", "law"}),
        target_kinds=frozenset({"variable", "entity"}),
        cardinality="many-to-many",
        acyclic=False,
    ),
    EngineeringRelationship.VALID_FOR: RelationshipSpec(
        relationship=EngineeringRelationship.VALID_FOR,
        definition="Applicability to a component, fluid, or regime.",
        source_kinds=frozenset({"relation"}),
        target_kinds=frozenset({"component", "material", "process"}),
        cardinality="many-to-many",
        acyclic=False,
    ),
    EngineeringRelationship.INVALID_FOR: RelationshipSpec(
        relationship=EngineeringRelationship.INVALID_FOR,
        definition="Explicit non-applicability.",
        source_kinds=frozenset({"relation"}),
        target_kinds=frozenset({"component", "material", "process"}),
        cardinality="many-to-many",
        acyclic=False,
    ),
    EngineeringRelationship.MEASURED_BY: RelationshipSpec(
        relationship=EngineeringRelationship.MEASURED_BY,
        definition="Quantity measured by an experiment or instrument.",
        source_kinds=frozenset({"property", "variable"}),
        target_kinds=frozenset({"experiment"}),
        cardinality="many-to-many",
        acyclic=False,
    ),
    EngineeringRelationship.VALIDATED_BY: RelationshipSpec(
        relationship=EngineeringRelationship.VALIDATED_BY,
        definition="Supported by experiment or simulation evidence.",
        source_kinds=frozenset({"relation"}),
        target_kinds=frozenset({"experiment", "simulation"}),
        cardinality="many-to-many",
        acyclic=False,
    ),
    EngineeringRelationship.SUPERSEDES: RelationshipSpec(
        relationship=EngineeringRelationship.SUPERSEDES,
        definition="Newer approved entity replaces a historical one.",
        source_kinds=frozenset({"entity"}),
        target_kinds=frozenset({"entity"}),
        cardinality="one-to-one",
        acyclic=True,
    ),
    EngineeringRelationship.CONTRADICTS: RelationshipSpec(
        relationship=EngineeringRelationship.CONTRADICTS,
        definition="Sources disagree; both claims are retained.",
        source_kinds=frozenset({"entity"}),
        target_kinds=frozenset({"entity"}),
        cardinality="many-to-many",
        acyclic=False,
    ),
    EngineeringRelationship.SUPPORTS: RelationshipSpec(
        relationship=EngineeringRelationship.SUPPORTS,
        definition="Evidence or citation supporting an entity.",
        source_kinds=frozenset({"document", "experiment", "simulation"}),
        target_kinds=frozenset({"entity"}),
        cardinality="many-to-many",
        acyclic=False,
    ),
    EngineeringRelationship.REQUIRES: RelationshipSpec(
        relationship=EngineeringRelationship.REQUIRES,
        definition="Requires an assumption or precondition.",
        source_kinds=frozenset({"relation", "simulation"}),
        target_kinds=frozenset({"assumption", "boundary_condition"}),
        cardinality="many-to-many",
        acyclic=True,
    ),
    EngineeringRelationship.CAUSES: RelationshipSpec(
        relationship=EngineeringRelationship.CAUSES,
        definition="Causal engineering mechanism.",
        source_kinds=frozenset({"process", "failure"}),
        target_kinds=frozenset({"failure", "effect"}),
        cardinality="many-to-many",
        acyclic=False,
    ),
    EngineeringRelationship.MITIGATES: RelationshipSpec(
        relationship=EngineeringRelationship.MITIGATES,
        definition="Design rule or process that reduces a failure mode.",
        source_kinds=frozenset({"design_rule", "process"}),
        target_kinds=frozenset({"failure"}),
        cardinality="many-to-many",
        acyclic=False,
    ),
}


def relationship_spec(relationship: EngineeringRelationship) -> RelationshipSpec:
    return _SPECS[relationship]
