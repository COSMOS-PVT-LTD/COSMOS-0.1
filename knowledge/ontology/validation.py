"""Ontology validation helpers for KG-BLOCK-008."""

from __future__ import annotations

import re
from collections.abc import Sequence

from knowledge.ontology.exceptions import OntologyValidationError, TaxonomyCycleError
from knowledge.ontology.models import TaxonomyEdge

__all__ = (
    "canonical_name_key",
    "normalize_observed_term",
    "validate_taxonomy_edge",
    "would_create_cycle",
)

_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_observed_term(label: str) -> str:
    """
    Normalize whitespace in an observed engineering label.

    Does not case-fold or alter engineering symbols (e.g. CO vs Co).
    """

    cleaned = label.strip()

    if not cleaned:
        raise ValueError("label must not be blank.")

    return _WHITESPACE_PATTERN.sub(" ", cleaned)


def canonical_name_key(name: str) -> str:
    """Return the case-insensitive canonical-name lookup key."""

    return normalize_observed_term(name).casefold()


def would_create_cycle(
    *,
    parent_term_id: str,
    child_term_id: str,
    edges: Sequence[TaxonomyEdge],
) -> bool:
    """Return True when adding parent→child would create a taxonomy cycle."""

    adjacency: dict[str, set[str]] = {}

    for edge in edges:
        adjacency.setdefault(edge.parent_term_id, set()).add(edge.child_term_id)

    adjacency.setdefault(parent_term_id, set()).add(child_term_id)

    stack = [child_term_id]
    visited: set[str] = set()

    while stack:
        current = stack.pop()

        if current == parent_term_id:
            return True

        if current in visited:
            continue

        visited.add(current)
        stack.extend(sorted(adjacency.get(current, set())))

    return False


def validate_taxonomy_edge(
    edge: TaxonomyEdge,
    *,
    existing_edges: Sequence[TaxonomyEdge],
) -> None:
    """Validate a taxonomy edge against cycle and duplicate constraints."""

    if not isinstance(edge, TaxonomyEdge):
        raise OntologyValidationError(
            "edge must be a TaxonomyEdge instance."
        )

    for existing in existing_edges:
        if (
            existing.parent_term_id == edge.parent_term_id
            and existing.child_term_id == edge.child_term_id
        ):
            raise TaxonomyCycleError(
                "Duplicate taxonomy parent-child edge is not permitted."
            )

    if would_create_cycle(
        parent_term_id=edge.parent_term_id,
        child_term_id=edge.child_term_id,
        edges=existing_edges,
    ):
        raise TaxonomyCycleError(
            "Taxonomy edge would create a hierarchy cycle."
        )
