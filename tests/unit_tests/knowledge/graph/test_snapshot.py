"""Unit tests for knowledge.graph.snapshot."""

from __future__ import annotations

import pytest

from knowledge.graph import (
    GraphNode,
    GraphNodeIdentity,
    GraphValidationError,
    ImmutableGraphRecord,
)
from knowledge.graph.snapshot import (
    GraphSnapshotMetadata,
    build_snapshot_id,
    create_graph_snapshot,
    snapshots_are_equivalent,
)


def _empty_record() -> ImmutableGraphRecord:
    return ImmutableGraphRecord(nodes=(), relationships=())


def test_build_snapshot_id_format() -> None:
    """Snapshot identifiers must follow KG-SNAPSHOT-####."""

    assert build_snapshot_id(1) == "KG-SNAPSHOT-0001"
    assert build_snapshot_id(42) == "KG-SNAPSHOT-0042"


def test_create_graph_snapshot_has_deterministic_identity() -> None:
    """Equivalent records must produce equivalent snapshot content."""

    first = create_graph_snapshot(_empty_record(), sequence_number=1)
    second = create_graph_snapshot(_empty_record(), sequence_number=2)

    assert snapshots_are_equivalent(first, second)
    assert first.identity.snapshot_id != second.identity.snapshot_id


def test_create_graph_snapshot_rejects_digest_mismatch() -> None:
    """Manually supplied digests must match record content."""

    record = ImmutableGraphRecord(
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

    snapshot = create_graph_snapshot(record, sequence_number=1)

    with pytest.raises(GraphValidationError):
        type(snapshot)(
            identity=type(snapshot.identity)(
                snapshot_id=snapshot.identity.snapshot_id,
                content_digest="a" * 64,
                sequence_number=1,
            ),
            record=record,
            metadata=GraphSnapshotMetadata(),
        )


def test_snapshot_metadata_mapping() -> None:
    """Snapshot metadata must serialize optional version fields."""

    snapshot = create_graph_snapshot(
        _empty_record(),
        sequence_number=3,
        metadata=GraphSnapshotMetadata(
            ontology_version="ontology-0.1",
            source_registry_version="registry-0.1",
        ),
    )

    mapping = snapshot.to_mapping()

    assert mapping["metadata"] == {
        "ontology_version": "ontology-0.1",
        "source_registry_version": "registry-0.1",
    }


def test_snapshot_metadata_does_not_affect_content_digest() -> None:
    """Snapshot metadata must remain outside canonical content digest identity."""

    record = _empty_record()
    bare = create_graph_snapshot(record, sequence_number=1)
    annotated = create_graph_snapshot(
        record,
        sequence_number=2,
        metadata=GraphSnapshotMetadata(
            ontology_version="ontology-0.1",
            source_registry_version="registry-0.1",
        ),
    )

    assert bare.identity.content_digest == annotated.identity.content_digest
    assert snapshots_are_equivalent(bare, annotated)
