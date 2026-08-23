"""Ontology relationship rule operations for KG-027."""

from __future__ import annotations

from knowledge.ontology.exceptions import OntologyValidationError
from knowledge.ontology.models import (
    OntologyRelationshipRule,
    OntologyRelationshipRuleType,
    RelationshipValidationResult,
)
from knowledge.ontology.registry import OntologyRegistry

__all__ = (
    "register_relationship_rule",
    "validate_relationship",
)


def register_relationship_rule(
    registry: OntologyRegistry,
    rule: OntologyRelationshipRule,
) -> OntologyRelationshipRule:
    """Register a deterministic ontology relationship compatibility rule."""

    if not isinstance(registry, OntologyRegistry):
        raise OntologyValidationError(
            "registry must be an OntologyRegistry instance."
        )

    registry.register_relationship_rule(rule)

    return rule


def validate_relationship(
    registry: OntologyRegistry,
    *,
    source_term_id: str,
    target_term_id: str,
    relationship_type: OntologyRelationshipRuleType,
) -> RelationshipValidationResult:
    """Validate whether a relationship is permitted between ontology terms."""

    if not isinstance(registry, OntologyRegistry):
        raise OntologyValidationError(
            "registry must be an OntologyRegistry instance."
        )

    return registry.validate_relationship(
        source_term_id=source_term_id,
        target_term_id=target_term_id,
        relationship_type=relationship_type,
    )


def explain_rejection(result: RelationshipValidationResult) -> str:
    """Return a human-readable rejection reason."""

    if result.permitted:
        return "Relationship permitted."

    if not result.reason:
        return "Relationship rejected by ontology rule policy."

    return result.reason
