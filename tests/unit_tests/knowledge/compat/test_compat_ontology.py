"""COMPAT-005 — OntologyManager facade tests."""

from __future__ import annotations

from knowledge.graph.entity import CanonicalEntityType
from knowledge.ontology import OntologyAlias, OntologyTerm
from knowledge.ontology.ontology_manager import OntologyManager


def test_ontology_manager_register_and_resolve_term() -> None:
    """OntologyManager must delegate term registration to OntologyRegistry."""

    manager = OntologyManager()
    manager.register_term(
        OntologyTerm(
            term_id="term-material-lox",
            canonical_name="Liquid Oxygen",
            entity_type=CanonicalEntityType.MATERIAL,
            aliases=(
                OntologyAlias(
                    alias="LOX",
                    canonical_term_id="term-material-lox",
                ),
            ),
        ),
    )

    resolved = manager.resolve_alias("LOX")

    assert resolved.term_id == "term-material-lox"
    assert manager.get_term("term-material-lox").canonical_name == "Liquid Oxygen"


def test_ontology_manager_list_terms() -> None:
    """OntologyManager.list_terms must expose registry contents."""

    manager = OntologyManager()
    manager.register_term(
        OntologyTerm(
            term_id="term-qty-pressure",
            canonical_name="Pressure",
            entity_type=CanonicalEntityType.QUANTITY,
        ),
    )

    terms = manager.list_terms()

    assert len(terms) == 1
    assert terms[0].term_id == "term-qty-pressure"


def test_ontology_manager_exposes_registry_metadata() -> None:
    """OntologyManager must expose registry metadata and backing registry."""

    manager = OntologyManager()

    assert manager.metadata.ontology_id
    assert manager.registry is manager._registry
