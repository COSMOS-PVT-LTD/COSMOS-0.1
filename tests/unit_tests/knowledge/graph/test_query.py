"""Unit tests for knowledge.graph query service."""

from __future__ import annotations

import pytest

from knowledge.graph import (
    GraphNode,
    GraphNodeIdentity,
    GraphQueryError,
    GraphQueryService,
    GraphRelationship,
    GraphValidationError,
    InMemoryGraphStore,
)


def _build_store() -> InMemoryGraphStore:
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
    store.add_node(
        GraphNode(
            identity=GraphNodeIdentity(
                node_id="node-002",
                node_type="Equation",
            ),
            properties={
                "lifecycle_state": "EXTRACTED",
                "document_id": "DOC-001",
            },
        ),
    )
    store.add_relationship(
        GraphRelationship(
            relationship_id="rel-001",
            relationship_type="references",
            source_node_id="node-001",
            target_node_id="node-002",
        ),
    )
    return store


def test_graph_query_service_neighbors() -> None:
    """Neighbor lookup must return connected nodes."""

    service = GraphQueryService(_build_store())

    neighbors = service.neighbors("node-001")

    assert len(neighbors) == 1
    assert neighbors[0].node_id == "node-002"


def test_graph_query_service_bounded_traversal() -> None:
    """Traversal must respect the depth bound."""

    service = GraphQueryService(_build_store())

    result = service.traverse("node-001", max_depth=1)

    assert {node.node_id for node in result.nodes} == {
        "node-001",
        "node-002",
    }
    assert len(result.relationships) == 1


def test_graph_query_service_provenance_metadata() -> None:
    """Provenance metadata must be retrievable from graph nodes."""

    service = GraphQueryService(_build_store())

    metadata = service.provenance_metadata("node-001")

    assert metadata["document_id"] == "DOC-001"
    assert metadata["lifecycle_state"] == "CANDIDATE"


def test_graph_query_service_traverse_respects_zero_depth() -> None:
    """Depth zero must return only the start node."""

    service = GraphQueryService(_build_store())

    result = service.traverse("node-001", max_depth=0)

    assert [node.node_id for node in result.nodes] == ["node-001"]
    assert result.relationships == ()
    assert result.depth_by_node_id == {"node-001": 0}


def test_graph_query_service_traverse_rejects_negative_depth() -> None:
    """Negative traversal depth must be rejected."""

    service = GraphQueryService(_build_store())

    with pytest.raises(GraphValidationError):
        service.traverse("node-001", max_depth=-1)


def test_graph_query_service_traverse_terminates_on_cycle() -> None:
    """Cyclic graphs must not cause unbounded traversal."""

    store = InMemoryGraphStore()
    for node_id in ("node-a", "node-b", "node-c"):
        store.add_node(
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id=node_id,
                    node_type="Quantity",
                ),
                properties={
                    "lifecycle_state": "CANDIDATE",
                    "document_id": "DOC-001",
                },
            ),
        )

    for relationship_id, source_id, target_id in (
        ("rel-ab", "node-a", "node-b"),
        ("rel-bc", "node-b", "node-c"),
        ("rel-ca", "node-c", "node-a"),
    ):
        store.add_relationship(
            GraphRelationship(
                relationship_id=relationship_id,
                relationship_type="references",
                source_node_id=source_id,
                target_node_id=target_id,
            ),
        )

    service = GraphQueryService(store)
    result = service.traverse("node-a", max_depth=10)

    assert {node.node_id for node in result.nodes} == {
        "node-a",
        "node-b",
        "node-c",
    }
    assert len(result.relationships) == 3


def test_graph_query_service_traverse_orders_nodes_deterministically() -> None:
    """Traversal output order must be stable across repeated calls."""

    service = GraphQueryService(_build_store())

    first = service.traverse("node-001", max_depth=1)
    second = service.traverse("node-001", max_depth=1)

    assert [node.node_id for node in first.nodes] == [
        node.node_id for node in second.nodes
    ]
    assert [rel.relationship_id for rel in first.relationships] == [
        rel.relationship_id for rel in second.relationships
    ]


def test_graph_query_service_subgraph_keeps_internal_edges_only() -> None:
    """Subgraph extraction must exclude relationships crossing the node boundary."""

    store = InMemoryGraphStore()
    for node_id in ("node-001", "node-002", "node-003"):
        store.add_node(
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id=node_id,
                    node_type="Quantity",
                ),
                properties={
                    "lifecycle_state": "CANDIDATE",
                    "document_id": "DOC-001",
                },
            ),
        )

    store.add_relationship(
        GraphRelationship(
            relationship_id="rel-internal",
            relationship_type="references",
            source_node_id="node-001",
            target_node_id="node-002",
        ),
    )
    store.add_relationship(
        GraphRelationship(
            relationship_id="rel-external",
            relationship_type="references",
            source_node_id="node-002",
            target_node_id="node-003",
        ),
    )

    service = GraphQueryService(store)
    record = service.subgraph({"node-001", "node-002"})

    assert {node.node_id for node in record.nodes} == {
        "node-001",
        "node-002",
    }
    assert [rel.relationship_id for rel in record.relationships] == [
        "rel-internal",
    ]


def test_graph_query_service_subgraph_empty_node_set() -> None:
    """An empty node selection must yield an empty immutable record."""

    service = GraphQueryService(_build_store())

    record = service.subgraph(set())

    assert record.nodes == ()
    assert record.relationships == ()


def test_graph_query_service_provenance_metadata_requires_fields() -> None:
    """Nodes without provenance-bearing properties must raise GraphQueryError."""

    store = InMemoryGraphStore()
    store.add_node(
        GraphNode(
            identity=GraphNodeIdentity(
                node_id="node-bare",
                node_type="Quantity",
            ),
        ),
    )

    service = GraphQueryService(store)

    with pytest.raises(GraphQueryError):
        service.provenance_metadata("node-bare")
