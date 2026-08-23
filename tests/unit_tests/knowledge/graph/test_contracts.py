"""Unit tests for knowledge.graph contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from knowledge.graph import (
    GraphNode,
    GraphNodeIdentity,
    GraphRecord,
    GraphRelationship,
    GraphValidationError,
    ImmutableGraphRecord,
    ProvenanceReference,
    is_property_value,
    normalize_properties,
)


def _make_node(
    node_id: str = "node-001",
    node_type: str = "Quantity",
) -> GraphNode:
    return GraphNode(
        identity=GraphNodeIdentity(
            node_id=node_id,
            node_type=node_type,
        ),
    )


def _make_relationship(
    *,
    relationship_id: str = "rel-001",
    relationship_type: str = "references",
    source_node_id: str = "node-001",
    target_node_id: str = "node-002",
) -> GraphRelationship:
    return GraphRelationship(
        relationship_id=relationship_id,
        relationship_type=relationship_type,
        source_node_id=source_node_id,
        target_node_id=target_node_id,
    )


def test_public_imports_from_knowledge_graph() -> None:
    """Public graph contract symbols must be importable from knowledge.graph."""

    from knowledge import graph as knowledge_graph

    assert knowledge_graph.GraphNode is GraphNode
    assert knowledge_graph.ImmutableGraphRecord is ImmutableGraphRecord


def test_graph_node_identity_is_deterministic() -> None:
    """Equal identities must compare equal regardless of construction order."""

    first = GraphNodeIdentity(node_id="QTY-001", node_type="Quantity")
    second = GraphNodeIdentity(node_id="QTY-001", node_type="Quantity")

    assert first == second
    assert hash(first) == hash(second)


def test_graph_node_identity_rejects_blank_values() -> None:
    """Blank node identifiers and types must be rejected."""

    with pytest.raises(GraphValidationError):
        GraphNodeIdentity(node_id="   ", node_type="Quantity")

    with pytest.raises(GraphValidationError):
        GraphNodeIdentity(node_id="QTY-001", node_type="   ")


def test_graph_node_valid_construction_and_immutability() -> None:
    """GraphNode must validate and remain immutable."""

    node = GraphNode(
        identity=GraphNodeIdentity(
            node_id="QTY-001",
            node_type="Quantity",
        ),
        properties={"symbol": "Pc"},
    )

    assert node.node_id == "QTY-001"
    assert node.node_type == "Quantity"
    assert node.properties["symbol"] == "Pc"

    with pytest.raises(FrozenInstanceError):
        node.properties = {"symbol": "P"}  # type: ignore[misc]


def test_graph_node_equality_uses_identity() -> None:
    """Graph nodes with matching identity and properties must compare equal."""

    left = _make_node()
    right = _make_node()
    different_type = GraphNode(
        identity=GraphNodeIdentity(
            node_id="node-001",
            node_type="Variable",
        ),
    )

    assert left == right
    assert left != different_type


def test_graph_node_same_identity_different_properties() -> None:
    """GraphNode equality includes properties, not identity fields alone."""

    identity = GraphNodeIdentity(node_id="node-001", node_type="Quantity")
    with_properties = GraphNode(
        identity=identity,
        properties={"symbol": "Pc"},
    )
    without_properties = GraphNode(identity=identity)

    assert with_properties != without_properties


def test_graph_node_hash_stable() -> None:
    """GraphNode hash must remain stable for an unchanged instance."""

    node = GraphNode(
        identity=GraphNodeIdentity(node_id="QTY-001", node_type="Quantity"),
        properties={"symbol": "Pc"},
    )

    assert hash(node) == hash(node)

    equivalent = GraphNode(
        identity=GraphNodeIdentity(node_id="QTY-001", node_type="Quantity"),
        properties={"symbol": "Pc"},
    )

    assert hash(node) == hash(equivalent)


def test_graph_relationship_valid_construction_and_direction() -> None:
    """Relationships must preserve explicit direction."""

    relationship = _make_relationship()

    assert relationship.source_node_id == "node-001"
    assert relationship.target_node_id == "node-002"
    assert relationship.relationship_type == "references"


def test_graph_relationship_rejects_invalid_endpoints() -> None:
    """Missing relationship endpoints must be rejected."""

    with pytest.raises(GraphValidationError):
        GraphRelationship(
            relationship_id="rel-001",
            relationship_type="references",
            source_node_id="   ",
            target_node_id="node-002",
        )

    with pytest.raises(GraphValidationError):
        GraphRelationship(
            relationship_id="rel-001",
            relationship_type="references",
            source_node_id="node-001",
            target_node_id="",
        )


def test_graph_relationship_rejects_empty_relationship_id() -> None:
    """Blank relationship identifiers must be rejected."""

    with pytest.raises(GraphValidationError):
        GraphRelationship(
            relationship_id="   ",
            relationship_type="references",
            source_node_id="node-001",
            target_node_id="node-002",
        )


def test_graph_relationship_rejects_empty_relationship_type() -> None:
    """Blank relationship types must be rejected."""

    with pytest.raises(GraphValidationError):
        GraphRelationship(
            relationship_id="rel-001",
            relationship_type="",
            source_node_id="node-001",
            target_node_id="node-002",
        )


def test_graph_relationship_equality_is_structural() -> None:
    """Equal relationships with the same endpoints must compare equal."""

    left = _make_relationship()
    right = _make_relationship()

    assert left == right
    assert hash(left) == hash(right)


def test_provenance_reference_minimal_valid_anchor() -> None:
    """A provenance reference may be anchored by a single identifier."""

    provenance = ProvenanceReference(document_id="DOC-001")

    assert provenance.document_id == "DOC-001"
    assert provenance.page is None


def test_provenance_reference_supports_location_anchors() -> None:
    """Provenance may include page, section, and equation anchors."""

    provenance = ProvenanceReference(
        source_id="SRC-001",
        document_id="DOC-001",
        page=12,
        section="3.2",
        equation="eq-7",
        location_anchor="page-12-eq-7",
    )

    assert provenance.page == 12
    assert provenance.equation == "eq-7"
    assert provenance.location_anchor == "page-12-eq-7"


def test_provenance_reference_rejects_empty_reference() -> None:
    """Completely empty provenance references must be rejected."""

    with pytest.raises(GraphValidationError):
        ProvenanceReference()


def test_provenance_reference_rejects_invalid_page() -> None:
    """Non-positive page anchors must be rejected."""

    with pytest.raises(GraphValidationError):
        ProvenanceReference(document_id="DOC-001", page=0)


def test_property_value_helper_and_normalization() -> None:
    """Property normalization must accept scalar values only."""

    assert is_property_value("value")
    assert is_property_value(1)
    assert is_property_value(1.5)
    assert is_property_value(True)
    assert is_property_value(None)
    assert not is_property_value({"nested": True})

    normalized = normalize_properties({"unit": "Pa", "exact": True})

    assert normalized["unit"] == "Pa"
    assert normalized["exact"] is True


def test_normalize_properties_rejects_blank_keys() -> None:
    """Property keys must be non-blank strings."""

    with pytest.raises(GraphValidationError):
        normalize_properties({"": "value"})


def test_normalize_properties_rejects_unsupported_types() -> None:
    """Property values must remain scalar per the PropertyValue contract."""

    with pytest.raises(GraphValidationError):
        normalize_properties({"nested": {"key": "value"}})

    with pytest.raises(GraphValidationError):
        normalize_properties({"items": [1, 2, 3]})

    with pytest.raises(GraphValidationError):
        normalize_properties({"handler": object()})


def test_immutable_graph_record_validates_unique_nodes() -> None:
    """Graph records must reject duplicate node identifiers."""

    node = _make_node()

    with pytest.raises(GraphValidationError):
        ImmutableGraphRecord(
            nodes=(node, node),
            relationships=(),
        )


def test_immutable_graph_record_validates_relationship_endpoints() -> None:
    """Relationship endpoints must reference existing nodes."""

    source = _make_node(node_id="node-001")
    relationship = _make_relationship(
        source_node_id="node-001",
        target_node_id="missing-node",
    )

    with pytest.raises(GraphValidationError):
        ImmutableGraphRecord(
            nodes=(source,),
            relationships=(relationship,),
        )


def test_immutable_graph_record_satisfies_graph_record_protocol() -> None:
    """ImmutableGraphRecord must satisfy the GraphRecord protocol."""

    source = _make_node(node_id="node-001")
    target = _make_node(node_id="node-002", node_type="Unit")
    relationship = _make_relationship(
        source_node_id="node-001",
        target_node_id="node-002",
    )

    record: GraphRecord = ImmutableGraphRecord(
        nodes=(source, target),
        relationships=(relationship,),
    )

    assert len(record.nodes) == 2
    assert len(record.relationships) == 1


def test_contract_mappings_are_deterministic() -> None:
    """Serialization-friendly mappings must preserve contract fields."""

    node = _make_node()
    relationship = _make_relationship()
    provenance = ProvenanceReference(document_id="DOC-001", page=3)
    record = ImmutableGraphRecord(
        nodes=(node, _make_node(node_id="node-002", node_type="Unit")),
        relationships=(relationship,),
    )

    assert node.to_mapping() == {
        "node_id": "node-001",
        "node_type": "Quantity",
        "properties": {},
    }
    assert relationship.to_mapping()["relationship_type"] == "references"
    assert provenance.to_mapping() == {
        "document_id": "DOC-001",
        "page": 3,
    }
    assert record.to_mapping()["nodes"][0]["node_id"] == "node-001"
