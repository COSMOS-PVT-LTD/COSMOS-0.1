"""Unit tests for knowledge.graph.relationship."""

from __future__ import annotations

import pytest

from knowledge.graph import (
    GraphRelationship,
    GraphValidationError,
    ProvenanceReference,
)
from knowledge.graph.exceptions import GraphContractError
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.graph.relationship import GraphEntityRelationshipRecord


def test_graph_entity_relationship_record_valid_construction() -> None:
    """Relationship adapters must preserve wrapped relationship data."""

    relationship = GraphRelationship(
        relationship_id="rel-001",
        relationship_type="references",
        source_node_id="node-001",
        target_node_id="node-002",
    )

    record = GraphEntityRelationshipRecord(
        relationship=relationship,
        provenance=ProvenanceReference(document_id="DOC-001"),
    )

    assert record.relationship.relationship_id == "rel-001"
    assert isinstance(record.provenance, ProvenanceReference)


def test_graph_entity_relationship_record_supports_source_provenance() -> None:
    """Relationship adapters may carry composite provenance records."""

    record = GraphEntityRelationshipRecord(
        relationship=GraphRelationship(
            relationship_id="rel-002",
            relationship_type="derived_from",
            source_node_id="node-001",
            target_node_id="node-002",
        ),
        provenance=SourceProvenanceRecord(
            anchor=ProvenanceReference(source_id="SRC-001"),
        ),
    )

    assert isinstance(record.provenance, SourceProvenanceRecord)


def test_graph_entity_relationship_record_rejects_invalid_provenance() -> None:
    """Invalid provenance types must be rejected."""

    with pytest.raises(GraphValidationError):
        GraphEntityRelationshipRecord(
            relationship=GraphRelationship(
                relationship_id="rel-003",
                relationship_type="references",
                source_node_id="node-001",
                target_node_id="node-002",
            ),
            provenance="invalid",  # type: ignore[arg-type]
        )


def test_validate_entity_endpoints_accepts_matching_ids() -> None:
    """Endpoint validation must succeed for matching identifiers."""

    record = GraphEntityRelationshipRecord(
        relationship=GraphRelationship(
            relationship_id="rel-004",
            relationship_type="references",
            source_node_id="node-001",
            target_node_id="node-002",
        ),
    )

    record.validate_entity_endpoints("node-001", "node-002")


def test_validate_entity_endpoints_rejects_mismatched_source() -> None:
    """Endpoint validation must reject mismatched source identifiers."""

    record = GraphEntityRelationshipRecord(
        relationship=GraphRelationship(
            relationship_id="rel-005",
            relationship_type="references",
            source_node_id="node-001",
            target_node_id="node-002",
        ),
    )

    with pytest.raises(GraphContractError):
        record.validate_entity_endpoints("missing", "node-002")
