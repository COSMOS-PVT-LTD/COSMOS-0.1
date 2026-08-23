"""
COMPATIBILITY FACADE (KG-BLOCK-013 Phase B — COMPAT-005).

Frozen Part-3 ontology manager surface delegating to OntologyRegistry.
"""

from __future__ import annotations

from collections.abc import Sequence

from knowledge.ontology.models import (
    OntologyAlias,
    OntologyRelationshipRule,
    OntologyRelationshipRuleType,
    OntologyTerm,
    OntologyVersionMetadata,
    RelationshipValidationResult,
    TaxonomyEdge,
)
from knowledge.ontology.registry import OntologyRegistry

__all__ = ("OntologyManager",)


class OntologyManager:
    """Legacy ontology manager facade over the canonical OntologyRegistry."""

    def __init__(self, registry: OntologyRegistry | None = None) -> None:
        self._registry = registry or OntologyRegistry()

    @property
    def registry(self) -> OntologyRegistry:
        return self._registry

    @property
    def metadata(self) -> OntologyVersionMetadata:
        return self._registry.metadata

    def register_term(self, term: OntologyTerm) -> None:
        self._registry.register_term(term)

    def get_term(self, term_id: str) -> OntologyTerm:
        return self._registry.get_term(term_id)

    def resolve_alias(self, alias: str) -> OntologyTerm:
        return self._registry.resolve_alias(alias)

    def register_alias(self, alias: OntologyAlias) -> None:
        self._registry.register_alias(alias)

    def register_taxonomy_edge(self, edge: TaxonomyEdge) -> None:
        self._registry.register_taxonomy_edge(edge)

    def register_relationship_rule(self, rule: OntologyRelationshipRule) -> None:
        self._registry.register_relationship_rule(rule)

    def validate_relationship(
        self,
        *,
        source_term_id: str,
        target_term_id: str,
        relationship_type: OntologyRelationshipRuleType,
    ) -> RelationshipValidationResult:
        return self._registry.validate_relationship(
            source_term_id=source_term_id,
            target_term_id=target_term_id,
            relationship_type=relationship_type,
        )

    def list_terms(self) -> Sequence[OntologyTerm]:
        return self._registry.list_terms()
