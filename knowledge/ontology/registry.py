"""
COSMOS Knowledge Foundation

Module:
    knowledge.ontology.registry

Purpose:
    In-memory ontology registry for canonical terms, aliases, taxonomy, and rules.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence

from knowledge.ontology.exceptions import (
    AliasConflictError,
    DuplicateOntologyTermError,
    OntologyRelationshipError,
    OntologyTermNotFoundError,
    OntologyValidationError,
)
from knowledge.ontology.identity import registry_state_digest
from knowledge.ontology.models import (
    OntologyAlias,
    OntologyRelationshipRule,
    OntologyRelationshipRuleType,
    OntologyRelationshipType,
    OntologyTerm,
    OntologyVersionMetadata,
    RelationshipValidationResult,
    TaxonomyEdge,
)
from knowledge.ontology.validation import (
    canonical_name_key,
    normalize_observed_term,
    validate_taxonomy_edge,
)

__all__ = (
    "DuplicateOntologyTermError",
    "OntologyRegistry",
    "OntologyTermNotFoundError",
)


class OntologyRegistry:
    """
    Controlled ontology registry without automatic ontology expansion.

    Provides deterministic lookup, alias resolution, taxonomy hierarchy, and
    relationship-rule validation for downstream normalization and graph layers.
    """

    def __init__(
        self,
        metadata: OntologyVersionMetadata | None = None,
    ) -> None:
        self._metadata = metadata or OntologyVersionMetadata(
            ontology_id="cosmos-kg-ontology",
            ontology_version="0.1.0",
        )
        self._terms: dict[str, OntologyTerm] = {}
        self._canonical_name_index: dict[str, str] = {}
        self._alias_index: dict[str, str] = {}
        self._aliases: dict[str, OntologyAlias] = {}
        self._taxonomy_edges: dict[tuple[str, str], TaxonomyEdge] = {}
        self._relationship_rules: dict[str, OntologyRelationshipRule] = {}

    @property
    def metadata(self) -> OntologyVersionMetadata:
        """Return ontology version metadata."""

        return self._metadata

    def register_term(self, term: OntologyTerm) -> None:
        """Register a canonical ontology term."""

        if not isinstance(term, OntologyTerm):
            raise OntologyValidationError(
                "term must be an OntologyTerm instance."
            )

        if term.term_id in self._terms:
            raise DuplicateOntologyTermError(
                f"Ontology term '{term.term_id}' is already registered."
            )

        name_key = canonical_name_key(term.canonical_name)

        if name_key in self._canonical_name_index:
            existing_term_id = self._canonical_name_index[name_key]
            raise DuplicateOntologyTermError(
                "Ontology canonical name "
                f"'{term.canonical_name}' conflicts with term "
                f"'{existing_term_id}'."
            )

        for alias in term.aliases:
            alias_key = normalize_observed_term(alias.alias)

            if alias_key in self._alias_index:
                raise AliasConflictError(
                    f"Ontology alias '{alias.alias}' is already registered."
                )

        self._terms[term.term_id] = term
        self._canonical_name_index[name_key] = term.term_id

        for alias in term.aliases:
            alias_key = normalize_observed_term(alias.alias)
            self._alias_index[alias_key] = term.term_id
            self._aliases[alias_key] = alias

    def register_alias(self, alias: OntologyAlias) -> None:
        """Register an alias for an existing canonical term."""

        if not isinstance(alias, OntologyAlias):
            raise OntologyValidationError(
                "alias must be an OntologyAlias instance."
            )

        self.get_term(alias.canonical_term_id)

        alias_key = normalize_observed_term(alias.alias)

        if alias_key in self._alias_index:
            existing_term_id = self._alias_index[alias_key]

            if existing_term_id != alias.canonical_term_id:
                raise AliasConflictError(
                    f"Ontology alias '{alias.alias}' conflicts with another term."
                )

            return

        self._alias_index[alias_key] = alias.canonical_term_id
        self._aliases[alias_key] = alias

    def get_term(self, term_id: str) -> OntologyTerm:
        """Return a registered ontology term by identifier."""

        try:
            return self._terms[term_id]
        except KeyError as exc:
            raise OntologyTermNotFoundError(
                f"Ontology term '{term_id}' was not found."
            ) from exc

    def resolve_alias(self, alias: str) -> OntologyTerm:
        """Resolve an alias to its canonical ontology term."""

        cleaned = alias.strip()

        if not cleaned:
            raise OntologyValidationError("alias must not be blank.")

        alias_key = normalize_observed_term(cleaned)
        term_id = self._alias_index.get(alias_key)

        if term_id is None:
            raise OntologyTermNotFoundError(
                f"Ontology alias '{alias}' was not found."
            )

        return self.get_term(term_id)

    def list_terms(self) -> Sequence[OntologyTerm]:
        """Return registered terms in deterministic term_id order."""

        return tuple(
            self._terms[term_id] for term_id in sorted(self._terms)
        )

    def list_aliases(self) -> tuple[OntologyAlias, ...]:
        """Return registered aliases in deterministic alias order."""

        return tuple(
            self._aliases[key]
            for key in sorted(self._aliases)
        )

    def list_relationship_types(self) -> Sequence[OntologyRelationshipType]:
        """Return supported relationship vocabulary in enum definition order."""

        return tuple(OntologyRelationshipType)

    def register_taxonomy_edge(self, edge: TaxonomyEdge) -> None:
        """Register a taxonomy parent-child edge."""

        if not isinstance(edge, TaxonomyEdge):
            raise OntologyValidationError(
                "edge must be a TaxonomyEdge instance."
            )

        self.get_term(edge.parent_term_id)
        self.get_term(edge.child_term_id)

        validate_taxonomy_edge(
            edge,
            existing_edges=tuple(self._taxonomy_edges.values()),
        )

        key = (edge.parent_term_id, edge.child_term_id)
        self._taxonomy_edges[key] = edge

    def children_of(self, term_id: str) -> Sequence[OntologyTerm]:
        """Return direct child terms in deterministic order."""

        self.get_term(term_id)
        child_ids = sorted(
            edge.child_term_id
            for edge in self._taxonomy_edges.values()
            if edge.parent_term_id == term_id
        )

        return tuple(self.get_term(child_id) for child_id in child_ids)

    def parents_of(self, term_id: str) -> Sequence[OntologyTerm]:
        """Return direct parent terms in deterministic order."""

        self.get_term(term_id)
        parent_ids = sorted(
            edge.parent_term_id
            for edge in self._taxonomy_edges.values()
            if edge.child_term_id == term_id
        )

        return tuple(self.get_term(parent_id) for parent_id in parent_ids)

    def ancestors_of(self, term_id: str) -> Sequence[OntologyTerm]:
        """Return ancestor terms in deterministic breadth-first order."""

        self.get_term(term_id)
        ancestors: list[OntologyTerm] = []
        seen: set[str] = set()
        queue: deque[str] = deque(
            parent.term_id for parent in self.parents_of(term_id)
        )

        while queue:
            current_id = queue.popleft()

            if current_id in seen:
                continue

            seen.add(current_id)
            term = self.get_term(current_id)
            ancestors.append(term)
            queue.extend(parent.term_id for parent in self.parents_of(current_id))

        return tuple(ancestors)

    def descendants_of(self, term_id: str) -> Sequence[OntologyTerm]:
        """Return descendant terms in deterministic breadth-first order."""

        self.get_term(term_id)
        descendants: list[OntologyTerm] = []
        seen: set[str] = set()
        queue: deque[str] = deque(
            child.term_id for child in self.children_of(term_id)
        )

        while queue:
            current_id = queue.popleft()

            if current_id in seen:
                continue

            seen.add(current_id)
            term = self.get_term(current_id)
            descendants.append(term)
            queue.extend(child.term_id for child in self.children_of(current_id))

        return tuple(descendants)

    def register_relationship_rule(
        self,
        rule: OntologyRelationshipRule,
    ) -> None:
        """Register an ontology relationship compatibility rule."""

        if not isinstance(rule, OntologyRelationshipRule):
            raise OntologyValidationError(
                "rule must be an OntologyRelationshipRule instance."
            )

        if rule.rule_id in self._relationship_rules:
            raise OntologyRelationshipError(
                f"Relationship rule '{rule.rule_id}' is already registered."
            )

        if rule.source_term_id is not None:
            self.get_term(rule.source_term_id)
        if rule.target_term_id is not None:
            self.get_term(rule.target_term_id)

        self._relationship_rules[rule.rule_id] = rule

    def validate_relationship(
        self,
        *,
        source_term_id: str,
        target_term_id: str,
        relationship_type: OntologyRelationshipRuleType,
    ) -> RelationshipValidationResult:
        """Validate whether a relationship is permitted between ontology terms."""

        source_term = self.get_term(source_term_id)
        target_term = self.get_term(target_term_id)

        for rule in sorted(
            self._relationship_rules.values(),
            key=lambda item: item.rule_id,
        ):
            if rule.relationship_type is not relationship_type:
                continue

            if rule.source_term_id is not None and rule.source_term_id != source_term_id:
                continue

            if rule.target_term_id is not None and rule.target_term_id != target_term_id:
                continue

            if source_term.entity_type is not rule.source_entity_type:
                continue

            if target_term.entity_type is not rule.target_entity_type:
                continue

            return RelationshipValidationResult(
                permitted=True,
                relationship_type=relationship_type,
                source_term_id=source_term_id,
                target_term_id=target_term_id,
                rule_id=rule.rule_id,
                reason=f"Permitted by rule '{rule.rule_id}'.",
            )

        return RelationshipValidationResult(
            permitted=False,
            relationship_type=relationship_type,
            source_term_id=source_term_id,
            target_term_id=target_term_id,
            reason="No matching ontology relationship rule found.",
        )

    def registry_digest(self) -> str:
        """Return a deterministic digest of the current registry state."""

        parts: list[str] = [
            self._metadata.ontology_id,
            self._metadata.ontology_version,
        ]

        for term in self.list_terms():
            parts.append(term.term_id)
            parts.append(term.canonical_name)
            parts.append(term.entity_type.value)

        for alias in self.list_aliases():
            parts.append(alias.alias)
            parts.append(alias.canonical_term_id)

        for key in sorted(self._taxonomy_edges):
            edge = self._taxonomy_edges[key]
            parts.append(edge.parent_term_id)
            parts.append(edge.child_term_id)

        for rule_id in sorted(self._relationship_rules):
            rule = self._relationship_rules[rule_id]
            parts.append(rule.rule_id)
            parts.append(rule.relationship_type.value)
            parts.append(rule.source_entity_type.value)
            parts.append(rule.target_entity_type.value)

        return registry_state_digest(*parts)
