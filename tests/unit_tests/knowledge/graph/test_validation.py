"""Unit tests for knowledge.graph validation."""

from __future__ import annotations

import pytest

from knowledge.graph import (
    GraphLifecycleState,
    GraphNode,
    GraphNodeIdentity,
    GraphRecordValidator,
    GraphRelationship,
    GraphValidationError,
    ImmutableGraphRecord,
)


def test_graph_record_validator_accepts_valid_record() -> None:
    """Valid constructed records must pass validation."""

    record = ImmutableGraphRecord(
        nodes=(
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id="node-001",
                    node_type="Quantity",
                ),
                properties={
                    "lifecycle_state": GraphLifecycleState.CANDIDATE.value,
                    "document_id": "DOC-001",
                },
            ),
        ),
        relationships=(),
    )

    report = GraphRecordValidator().validate(record)

    assert report.is_valid


def test_graph_record_validator_rejects_missing_provenance_fields() -> None:
    """Nodes missing required provenance metadata must fail validation."""

    record = ImmutableGraphRecord(
        nodes=(
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id="node-001",
                    node_type="Quantity",
                ),
                properties={},
            ),
        ),
        relationships=(),
    )

    report = GraphRecordValidator().validate(record)

    assert not report.is_valid
    assert any(
        issue.code == "missing_node_property" for issue in report.issues
    )


def test_graph_record_validator_rejects_premature_approval() -> None:
    """Constructed graph nodes must not be approved automatically."""

    record = ImmutableGraphRecord(
        nodes=(
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id="node-001",
                    node_type="Quantity",
                ),
                properties={
                    "lifecycle_state": GraphLifecycleState.APPROVED.value,
                    "document_id": "DOC-001",
                },
            ),
        ),
        relationships=(),
    )

    with pytest.raises(GraphValidationError):
        GraphRecordValidator().validate_or_raise(record)


def test_graph_record_validator_flags_missing_relationship_endpoints() -> None:
    """Relationships with dangling endpoints must fail validation."""

    record = object.__new__(ImmutableGraphRecord)
    object.__setattr__(
        record,
        "nodes",
        (
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id="node-001",
                    node_type="Quantity",
                ),
                properties={
                    "lifecycle_state": GraphLifecycleState.CANDIDATE.value,
                    "document_id": "DOC-001",
                },
            ),
        ),
    )
    object.__setattr__(
        record,
        "relationships",
        (
            GraphRelationship(
                relationship_id="rel-001",
                relationship_type="references",
                source_node_id="node-001",
                target_node_id="missing",
            ),
        ),
    )

    report = GraphRecordValidator().validate(record)

    assert any(
        issue.code == "missing_target_endpoint" for issue in report.issues
    )


def test_graph_record_validator_rejects_invalid_lifecycle_state() -> None:
    """Unrecognized lifecycle values must fail validation."""

    record = ImmutableGraphRecord(
        nodes=(
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id="node-001",
                    node_type="Quantity",
                ),
                properties={
                    "lifecycle_state": "NOT_A_STATE",
                    "document_id": "DOC-001",
                },
            ),
        ),
        relationships=(),
    )

    report = GraphRecordValidator().validate(record)

    assert any(
        issue.code == "invalid_lifecycle_state" for issue in report.issues
    )


def test_graph_record_validator_flags_confirmed_conflict() -> None:
    """Confirmed conflict visibility must surface as a validation issue."""

    record = ImmutableGraphRecord(
        nodes=(
            GraphNode(
                identity=GraphNodeIdentity(
                    node_id="node-001",
                    node_type="Claim",
                ),
                properties={
                    "lifecycle_state": GraphLifecycleState.CANDIDATE.value,
                    "document_id": "DOC-001",
                    "conflict_visibility": "CONFIRMED_CONFLICT",
                },
            ),
        ),
        relationships=(),
    )

    report = GraphRecordValidator().validate(record)

    assert any(
        issue.code == "confirmed_conflict" for issue in report.issues
    )
