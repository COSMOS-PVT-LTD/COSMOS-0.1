"""Unit tests for knowledge.graph.serialization."""

from __future__ import annotations

import pytest

from knowledge.graph import (
    GraphNode,
    GraphNodeIdentity,
    GraphRelationship,
    GraphValidationError,
    ImmutableGraphRecord,
)
from knowledge.graph.serialization import (
    canonical_graph_record_digest,
    graph_record_from_mapping,
    graph_record_to_mapping,
)


def _sample_record() -> ImmutableGraphRecord:
    return ImmutableGraphRecord(
        nodes=(
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id="node-002",
                    node_type="Unit",
                ),
            ),
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id="node-001",
                    node_type="Quantity",
                ),
                properties={"symbol": "Pc"},
            ),
        ),
        relationships=(
            GraphRelationship(
                relationship_id="rel-001",
                relationship_type="references",
                source_node_id="node-001",
                target_node_id="node-002",
            ),
        ),
    )


def test_graph_record_to_mapping_orders_nodes_deterministically() -> None:
    """Serialized node order must be deterministic."""

    mapping = graph_record_to_mapping(_sample_record())
    node_ids = [node["node_id"] for node in mapping["nodes"]]  # type: ignore[index]

    assert node_ids == ["node-001", "node-002"]


def test_graph_record_round_trip_preserves_semantics() -> None:
    """Mappings must round-trip to semantically equivalent graph records."""

    original = _sample_record()
    restored = graph_record_from_mapping(
        graph_record_to_mapping(original),
    )

    assert canonical_graph_record_digest(restored) == (
        canonical_graph_record_digest(original)
    )
    assert {node.node_id for node in restored.nodes} == {
        node.node_id for node in original.nodes
    }
    assert len(restored.relationships) == len(original.relationships)


def test_canonical_graph_record_digest_is_deterministic() -> None:
    """Equivalent records must produce identical digests."""

    record = _sample_record()

    assert canonical_graph_record_digest(record) == (
        canonical_graph_record_digest(record)
    )


def test_graph_record_from_mapping_rejects_invalid_node() -> None:
    """Invalid node mappings must be rejected."""

    with pytest.raises(GraphValidationError):
        graph_record_from_mapping(
            {
                "nodes": [{"node_id": 1, "node_type": "Quantity"}],
                "relationships": [],
            }
        )


def test_canonical_digest_ignores_node_tuple_order() -> None:
    """Logically equivalent records must digest equally regardless of node order."""

    node_a = GraphNode(
        identity=GraphNodeIdentity(node_id="node-001", node_type="Quantity"),
        properties={"symbol": "Pc"},
    )
    node_b = GraphNode(
        identity=GraphNodeIdentity(node_id="node-002", node_type="Unit"),
    )
    forward = ImmutableGraphRecord(nodes=(node_a, node_b), relationships=())
    reverse = ImmutableGraphRecord(nodes=(node_b, node_a), relationships=())

    assert canonical_graph_record_digest(forward) == (
        canonical_graph_record_digest(reverse)
    )


def test_canonical_digest_ignores_property_key_order() -> None:
    """Property key insertion order must not affect the canonical digest."""

    first = ImmutableGraphRecord(
        nodes=(
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id="node-001",
                    node_type="Quantity",
                ),
                properties={"symbol": "Pc", "unit": "Pa"},
            ),
        ),
        relationships=(),
    )
    second = ImmutableGraphRecord(
        nodes=(
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id="node-001",
                    node_type="Quantity",
                ),
                properties={"unit": "Pa", "symbol": "Pc"},
            ),
        ),
        relationships=(),
    )

    assert canonical_graph_record_digest(first) == (
        canonical_graph_record_digest(second)
    )


def test_canonical_digest_changes_when_content_changes() -> None:
    """Different graph content must produce different digests."""

    baseline = ImmutableGraphRecord(
        nodes=(
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id="node-001",
                    node_type="Quantity",
                ),
            ),
        ),
        relationships=(),
    )
    changed = ImmutableGraphRecord(
        nodes=(
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id="node-001",
                    node_type="Quantity",
                ),
                properties={"symbol": "Pc"},
            ),
        ),
        relationships=(),
    )

    assert canonical_graph_record_digest(baseline) != (
        canonical_graph_record_digest(changed)
    )


def test_canonical_digest_ignores_relationship_tuple_order() -> None:
    """Relationship tuple order must not affect the canonical digest."""

    node_a = GraphNode(
        identity=GraphNodeIdentity(node_id="node-001", node_type="Quantity"),
    )
    node_b = GraphNode(
        identity=GraphNodeIdentity(node_id="node-002", node_type="Unit"),
    )
    rel_first = GraphRelationship(
        relationship_id="rel-001",
        relationship_type="references",
        source_node_id="node-001",
        target_node_id="node-002",
    )
    rel_second = GraphRelationship(
        relationship_id="rel-002",
        relationship_type="uses",
        source_node_id="node-002",
        target_node_id="node-001",
    )

    forward = ImmutableGraphRecord(
        nodes=(node_a, node_b),
        relationships=(rel_first, rel_second),
    )
    reverse = ImmutableGraphRecord(
        nodes=(node_a, node_b),
        relationships=(rel_second, rel_first),
    )

    assert canonical_graph_record_digest(forward) == (
        canonical_graph_record_digest(reverse)
    )
