"""Unit tests for knowledge.graph.repository."""

from __future__ import annotations

import pytest

from knowledge.graph import (
    GraphNode,
    GraphNodeIdentity,
    GraphRelationship,
    GraphStorageError,
    GraphValidationError,
    ImmutableGraphRecord,
)
from knowledge.graph.memory_store import InMemoryGraphStore
from knowledge.graph.repository import GraphStore


def _make_node(node_id: str) -> GraphNode:
    return GraphNode(
        identity=GraphNodeIdentity(
            node_id=node_id,
            node_type="Quantity",
        ),
    )


def test_in_memory_graph_store_satisfies_protocol() -> None:
    """The test double must satisfy the GraphStore protocol."""

    store: GraphStore = InMemoryGraphStore()

    assert isinstance(store, GraphStore)


def test_graph_store_add_and_get_node() -> None:
    """Nodes must be retrievable after insertion."""

    store = InMemoryGraphStore()
    node = _make_node("node-001")

    store.add_node(node)

    assert store.get_node("node-001") == node


def test_graph_store_rejects_duplicate_node() -> None:
    """Duplicate node identifiers must be rejected."""

    store = InMemoryGraphStore()
    store.add_node(_make_node("node-001"))

    with pytest.raises(GraphStorageError):
        store.add_node(_make_node("node-001"))


def test_graph_store_requires_existing_endpoints_for_relationship() -> None:
    """Relationships must reference existing nodes."""

    store = InMemoryGraphStore()
    relationship = GraphRelationship(
        relationship_id="rel-001",
        relationship_type="references",
        source_node_id="node-001",
        target_node_id="node-002",
    )

    with pytest.raises(GraphStorageError):
        store.add_relationship(relationship)


def test_graph_store_snapshot_and_restore_round_trip() -> None:
    """Snapshot and restore must preserve graph state."""

    store = InMemoryGraphStore()
    source = _make_node("node-001")
    target = _make_node("node-002")
    relationship = GraphRelationship(
        relationship_id="rel-001",
        relationship_type="references",
        source_node_id="node-001",
        target_node_id="node-002",
    )

    store.add_node(source)
    store.add_node(target)
    store.add_relationship(relationship)

    snapshot = store.snapshot()
    store.remove_node("node-001")

    store.restore(snapshot)

    assert store.get_node("node-001") == source
    assert len(store.list_relationships()) == 1


def test_empty_graph_store_snapshot_is_valid() -> None:
    """An empty store must produce a valid empty snapshot."""

    store = InMemoryGraphStore()

    snapshot = store.snapshot()

    assert snapshot.nodes == ()
    assert snapshot.relationships == ()


def test_restore_rejects_invalid_graph_record() -> None:
    """Restore must propagate validation failures from ImmutableGraphRecord."""

    store = InMemoryGraphStore()

    with pytest.raises(GraphValidationError):
        store.restore(
            ImmutableGraphRecord(
                nodes=(_make_node("node-001"),),
                relationships=(
                    GraphRelationship(
                        relationship_id="rel-001",
                        relationship_type="references",
                        source_node_id="node-001",
                        target_node_id="missing",
                    ),
                ),
            )
        )
