"""Taxonomy hierarchy operations for KG-026."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from knowledge.ontology.exceptions import OntologyValidationError
from knowledge.ontology.models import OntologyTerm, TaxonomyEdge

if TYPE_CHECKING:
    from knowledge.ontology.registry import OntologyRegistry

__all__ = (
    "ancestors_of",
    "children_of",
    "descendants_of",
    "parents_of",
    "register_taxonomy_edge",
)


def register_taxonomy_edge(
    registry: OntologyRegistry,
    *,
    parent_term_id: str,
    child_term_id: str,
) -> TaxonomyEdge:
    """Register a parent-child taxonomy edge with cycle prevention."""

    from knowledge.ontology.registry import OntologyRegistry as Registry

    if not isinstance(registry, Registry):
        raise OntologyValidationError(
            "registry must be an OntologyRegistry instance."
        )

    edge = TaxonomyEdge(
        parent_term_id=parent_term_id,
        child_term_id=child_term_id,
    )

    registry.register_taxonomy_edge(edge)

    return edge


def children_of(
    registry: OntologyRegistry,
    term_id: str,
) -> Sequence[OntologyTerm]:
    """Return direct child terms."""

    return registry.children_of(term_id)


def parents_of(
    registry: OntologyRegistry,
    term_id: str,
) -> Sequence[OntologyTerm]:
    """Return direct parent terms."""

    return registry.parents_of(term_id)


def ancestors_of(
    registry: OntologyRegistry,
    term_id: str,
) -> Sequence[OntologyTerm]:
    """Return ancestor terms in deterministic breadth-first order."""

    return registry.ancestors_of(term_id)


def descendants_of(
    registry: OntologyRegistry,
    term_id: str,
) -> Sequence[OntologyTerm]:
    """Return descendant terms in deterministic breadth-first order."""

    return registry.descendants_of(term_id)
