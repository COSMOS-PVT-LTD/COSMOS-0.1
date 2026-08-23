"""Unit tests for knowledge.graph.entity."""

from __future__ import annotations

import pytest

from knowledge.graph import GraphNode, GraphNodeIdentity, GraphValidationError
from knowledge.graph.entity import (
    CanonicalEntityReference,
    CanonicalEntityType,
    GraphEntityRecord,
)
from knowledge.graph.exceptions import GraphContractError


def test_canonical_entity_reference_is_deterministic() -> None:
    """Canonical references must compare equal for identical inputs."""

    first = CanonicalEntityReference(
        entity_id="QTY-001",
        entity_type=CanonicalEntityType.QUANTITY,
        model_name="quantity",
    )
    second = CanonicalEntityReference(
        entity_id="QTY-001",
        entity_type=CanonicalEntityType.QUANTITY,
        model_name="quantity",
    )

    assert first == second
    assert first.identity_key() == second.identity_key()


def test_canonical_entity_reference_rejects_unknown_model() -> None:
    """Only recognized canonical model names are permitted."""

    with pytest.raises(GraphValidationError):
        CanonicalEntityReference(
            entity_id="X-001",
            entity_type=CanonicalEntityType.OTHER,
            model_name="graph_quantity",
        )


def test_graph_entity_record_without_canonical_reference() -> None:
    """Graph entities may exist without a canonical reference."""

    record = GraphEntityRecord(
        node=GraphNode(
            identity=GraphNodeIdentity(
                node_id="node-001",
                node_type="Claim",
            ),
        ),
    )

    assert record.entity_id == "node-001"
    assert record.canonical_reference is None


def test_graph_entity_record_with_matching_canonical_reference() -> None:
    """Canonical references must align with graph node identity."""

    record = GraphEntityRecord(
        node=GraphNode(
            identity=GraphNodeIdentity(
                node_id="QTY-001",
                node_type="Quantity",
            ),
        ),
        canonical_reference=CanonicalEntityReference(
            entity_id="QTY-001",
            entity_type=CanonicalEntityType.QUANTITY,
            model_name="quantity",
        ),
    )

    assert record.entity_type == "Quantity"


def test_graph_entity_record_rejects_type_mismatch() -> None:
    """Mismatched node and canonical types must be rejected."""

    with pytest.raises(GraphContractError):
        GraphEntityRecord(
            node=GraphNode(
                identity=GraphNodeIdentity(
                    node_id="QTY-001",
                    node_type="Quantity",
                ),
            ),
            canonical_reference=CanonicalEntityReference(
                entity_id="QTY-001",
                entity_type=CanonicalEntityType.UNIT,
                model_name="unit",
            ),
        )


def test_graph_entity_record_rejects_identifier_mismatch() -> None:
    """Mismatched node and canonical identifiers must be rejected."""

    with pytest.raises(GraphContractError):
        GraphEntityRecord(
            node=GraphNode(
                identity=GraphNodeIdentity(
                    node_id="QTY-001",
                    node_type="Quantity",
                ),
            ),
            canonical_reference=CanonicalEntityReference(
                entity_id="QTY-002",
                entity_type=CanonicalEntityType.QUANTITY,
                model_name="quantity",
            ),
        )
