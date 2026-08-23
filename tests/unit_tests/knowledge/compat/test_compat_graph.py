"""COMPAT-004 — GraphManager facade tests."""

from __future__ import annotations

import pytest

from knowledge.extraction import CandidateEntityExtraction, ExtractedEntityKind
from knowledge.graph import GraphConstructionBatch, ProvenanceReference
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.exceptions import GraphQueryError
from knowledge.graph.graph_manager import GraphManager
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.ontology import OntologyRegistry, OntologyTerm


def _entity(label: str, extraction_id: str = "ENT-1") -> CandidateEntityExtraction:
    return CandidateEntityExtraction(
        extraction_id=extraction_id,
        document_id="DOC-001",
        extracted_label=label,
        entity_kind=ExtractedEntityKind.QUANTITY,
        canonical_entity_type=CanonicalEntityType.QUANTITY,
        provenance=SourceProvenanceRecord(
            anchor=ProvenanceReference(document_id="DOC-001", page=1),
        ),
    )


def test_graph_manager_construct_and_query() -> None:
    """GraphManager must construct a graph and expose query service."""

    manager = GraphManager()
    result = manager.construct(
        GraphConstructionBatch(entity_extractions=(_entity("Chamber Pressure"),)),
    )

    assert result.store is manager.store
    assert manager.query_service() is not None
    assert manager.store.get_node("ENT-1") is not None


def test_graph_manager_traverse_requires_constructed_graph() -> None:
    """GraphManager must reject traversal before construction."""

    manager = GraphManager()

    with pytest.raises(GraphQueryError):
        manager.traverse("ENT-1")


def test_graph_manager_traverse_after_construct() -> None:
    """GraphManager.traverse must delegate to GraphQueryService."""

    manager = GraphManager()
    manager.construct(
        GraphConstructionBatch(
            entity_extractions=(
                _entity("Chamber Pressure", "ENT-1"),
                _entity("LOX", "ENT-2"),
            ),
        ),
    )

    traversal = manager.traverse("ENT-1", max_depth=1)

    assert any(node.node_id == "ENT-1" for node in traversal.nodes)


def test_graph_manager_uses_provided_ontology_registry() -> None:
    """GraphManager must honor an injected OntologyRegistry."""

    registry = OntologyRegistry()
    registry.register_term(
        OntologyTerm(
            term_id="term-qty-pressure",
            canonical_name="Pressure",
            entity_type=CanonicalEntityType.QUANTITY,
        ),
    )
    manager = GraphManager(registry)

    assert manager.ontology_registry is registry
