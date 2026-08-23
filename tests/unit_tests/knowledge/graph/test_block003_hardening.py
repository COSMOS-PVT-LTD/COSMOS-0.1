"""KG-BLOCK-003 integration hardening tests."""

from __future__ import annotations

import importlib

import pytest

from knowledge.graph import (
    GraphConstructionBatch,
    GraphConstructor,
    GraphConstructionError,
    GraphQueryService,
    GraphRecordValidator,
    GraphStorageError,
    InMemoryGraphStore,
    graph_node_id_for_extraction,
)
from knowledge.graph.construction import GraphConstructor as DirectGraphConstructor
from knowledge.graph.exceptions import GraphConstructionError as DirectConstructionError


def test_graph_package_imports_without_extraction_cycle() -> None:
    """Importing graph contracts must not require eager extraction imports."""

    graph_module = importlib.import_module("knowledge.graph")

    assert hasattr(graph_module, "GraphStore")
    assert hasattr(graph_module, "GraphRecordValidator")


def test_lazy_construction_exports_resolve() -> None:
    """Construction symbols must resolve through lazy package exports."""

    assert graph_node_id_for_extraction("ENT-001") == "ENT-001"
    assert GraphConstructor is DirectGraphConstructor
    assert GraphConstructionError is DirectConstructionError


def test_extraction_import_after_graph_does_not_break_construction() -> None:
    """Extraction and graph packages must coexist without import failure."""

    importlib.import_module("knowledge.graph")
    extraction_module = importlib.import_module("knowledge.extraction")
    from knowledge.ontology import OntologyRegistry

    assert hasattr(extraction_module, "CandidateEntityExtraction")
    assert GraphConstructor(OntologyRegistry())


def test_in_memory_graph_store_lists_are_sorted() -> None:
    """Reference store listings must be deterministic."""

    from knowledge.graph import GraphNode, GraphNodeIdentity

    store = InMemoryGraphStore()
    for node_id in ("node-c", "node-a", "node-b"):
        store.add_node(
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id=node_id,
                    node_type="Quantity",
                ),
            ),
        )

    assert [node.node_id for node in store.list_nodes()] == [
        "node-a",
        "node-b",
        "node-c",
    ]


def test_constructed_graph_passes_record_validator() -> None:
    """End-to-end construction output must satisfy KG-015 validation rules."""

    from knowledge.extraction import (
        CandidateEntityExtraction,
        CandidateRelationshipExtraction,
        ExtractedEntityKind,
    )
    from knowledge.graph import ProvenanceReference
    from knowledge.graph.entity import CanonicalEntityType
    from knowledge.graph.provenance import SourceProvenanceRecord
    from knowledge.ontology import OntologyRegistry

    provenance = SourceProvenanceRecord(
        anchor=ProvenanceReference(document_id="DOC-001", page=1),
    )
    batch = GraphConstructionBatch(
        entity_extractions=(
            CandidateEntityExtraction(
                extraction_id="ENT-001",
                document_id="DOC-001",
                extracted_label="Pc",
                entity_kind=ExtractedEntityKind.QUANTITY,
                canonical_entity_type=CanonicalEntityType.QUANTITY,
                provenance=provenance,
            ),
        ),
        relationship_extractions=(
            CandidateRelationshipExtraction(
                relationship_id="REL-001",
                document_id="DOC-001",
                relationship_type="references",
                source_extraction_id="ENT-001",
                target_extraction_id="ENT-001",
                provenance=provenance,
            ),
        ),
    )

    result = GraphConstructor(OntologyRegistry()).construct(batch)
    report = GraphRecordValidator().validate(result.store.snapshot())

    assert report.is_valid


def test_graph_query_service_operates_on_graph_store_protocol() -> None:
    """Query service must work with any GraphStore implementation."""

    from knowledge.graph import GraphNode, GraphNodeIdentity

    store = InMemoryGraphStore()
    store.add_node(
        GraphNode(
            identity=GraphNodeIdentity(
                node_id="node-001",
                node_type="Quantity",
            ),
            properties={
                "lifecycle_state": "CANDIDATE",
                "document_id": "DOC-001",
            },
        ),
    )

    service = GraphQueryService(store)

    with pytest.raises(GraphStorageError):
        service.get_entity("missing")

    metadata = service.provenance_metadata("node-001")

    assert metadata["document_id"] == "DOC-001"
