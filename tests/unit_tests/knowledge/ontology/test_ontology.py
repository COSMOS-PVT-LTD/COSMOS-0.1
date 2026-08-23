"""Unit tests for knowledge.ontology registry."""

from __future__ import annotations

import pytest

from knowledge.graph.entity import CanonicalEntityType
from knowledge.ontology import (
    DuplicateOntologyTermError,
    OntologyAlias,
    OntologyRegistry,
    OntologyTerm,
    OntologyTermNotFoundError,
)


def test_ontology_registry_register_and_resolve_alias() -> None:
    """Ontology registry must resolve aliases deterministically."""

    registry = OntologyRegistry()
    term = OntologyTerm(
        term_id="term-quantity-pressure",
        canonical_name="Chamber Pressure",
        entity_type=CanonicalEntityType.QUANTITY,
        aliases=(
            OntologyAlias(
                alias="Pc",
                canonical_term_id="term-quantity-pressure",
            ),
        ),
    )

    registry.register_term(term)

    resolved = registry.resolve_alias("Pc")

    assert resolved.term_id == "term-quantity-pressure"


def test_ontology_registry_rejects_duplicate_term() -> None:
    """Duplicate ontology term identifiers must be rejected."""

    registry = OntologyRegistry()
    term = OntologyTerm(
        term_id="term-001",
        canonical_name="Example",
        entity_type=CanonicalEntityType.OTHER,
    )

    registry.register_term(term)

    with pytest.raises(DuplicateOntologyTermError):
        registry.register_term(term)


def test_ontology_registry_missing_alias_fails() -> None:
    """Missing aliases must raise OntologyTermNotFoundError."""

    registry = OntologyRegistry()

    with pytest.raises(OntologyTermNotFoundError):
        registry.resolve_alias("missing")
