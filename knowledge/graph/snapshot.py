"""
COSMOS Knowledge Foundation

Module:
    knowledge.graph.snapshot

Purpose:
    Deterministic graph snapshot and versioning contracts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from knowledge.graph.contracts import ImmutableGraphRecord
from knowledge.graph.exceptions import GraphValidationError
from knowledge.graph.serialization import (
    canonical_graph_record_digest,
    graph_record_to_mapping,
)

__all__ = (
    "GraphSnapshot",
    "GraphSnapshotIdentity",
    "GraphSnapshotMetadata",
    "build_snapshot_id",
    "create_graph_snapshot",
    "snapshots_are_equivalent",
)

_SNAPSHOT_ID_PATTERN = re.compile(r"^KG-SNAPSHOT-\d{4}$")


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise GraphValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise GraphValidationError(f"{field_name} must not be blank.")

    return cleaned


def _validate_optional_non_empty_string(
    field_name: str,
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return _validate_non_empty_string(field_name, value)


def _validate_sha256_digest(field_name: str, value: str) -> str:
    cleaned = _validate_non_empty_string(field_name, value)

    if len(cleaned) != 64 or any(
        character not in "0123456789abcdefABCDEF"
        for character in cleaned
    ):
        raise GraphValidationError(
            f"{field_name} must be a 64-character hexadecimal SHA-256 digest."
        )

    return cleaned.lower()


def build_snapshot_id(sequence_number: int) -> str:
    """Build a deterministic snapshot identifier."""

    if not isinstance(sequence_number, int) or isinstance(
        sequence_number,
        bool,
    ):
        raise GraphValidationError(
            "sequence_number must be an integer."
        )

    if sequence_number <= 0:
        raise GraphValidationError(
            "sequence_number must be a positive integer."
        )

    return f"KG-SNAPSHOT-{sequence_number:04d}"


def _validate_snapshot_id(snapshot_id: str) -> str:
    if not isinstance(snapshot_id, str):
        raise GraphValidationError("snapshot_id must be a string.")

    cleaned = snapshot_id.strip()

    if not _SNAPSHOT_ID_PATTERN.match(cleaned):
        raise GraphValidationError(
            "snapshot_id must match the KG-SNAPSHOT-#### format."
        )

    return cleaned


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphSnapshotMetadata:
    """
    Version metadata attached to a graph snapshot.

    Metadata is explicit and does not use wall-clock timestamps for identity.
    """

    ontology_version: str | None = None
    source_registry_version: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "ontology_version",
            _validate_optional_non_empty_string(
                "ontology_version",
                self.ontology_version,
            ),
        )
        object.__setattr__(
            self,
            "source_registry_version",
            _validate_optional_non_empty_string(
                "source_registry_version",
                self.source_registry_version,
            ),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {}

        if self.ontology_version is not None:
            payload["ontology_version"] = self.ontology_version
        if self.source_registry_version is not None:
            payload["source_registry_version"] = (
                self.source_registry_version
            )

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphSnapshotIdentity:
    """Deterministic identity for a graph snapshot."""

    snapshot_id: str
    content_digest: str
    sequence_number: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "snapshot_id",
            _validate_snapshot_id(self.snapshot_id),
        )
        object.__setattr__(
            self,
            "content_digest",
            _validate_sha256_digest("content_digest", self.content_digest),
        )

        if not isinstance(self.sequence_number, int) or isinstance(
            self.sequence_number,
            bool,
        ):
            raise GraphValidationError(
                "sequence_number must be an integer."
            )

        if self.sequence_number <= 0:
            raise GraphValidationError(
                "sequence_number must be a positive integer."
            )

        expected_snapshot_id = build_snapshot_id(self.sequence_number)

        if self.snapshot_id != expected_snapshot_id:
            raise GraphValidationError(
                "snapshot_id must match the provided sequence_number."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphSnapshot:
    """
    Immutable graph snapshot with deterministic identity semantics.

    Snapshot identity depends on the snapshot sequence and canonical graph
    content digest, not on process-local state.
    """

    identity: GraphSnapshotIdentity
    record: ImmutableGraphRecord
    metadata: GraphSnapshotMetadata = GraphSnapshotMetadata()

    def __post_init__(self) -> None:
        if not isinstance(self.identity, GraphSnapshotIdentity):
            raise GraphValidationError(
                "identity must be a GraphSnapshotIdentity instance."
            )

        if not isinstance(self.record, ImmutableGraphRecord):
            raise GraphValidationError(
                "record must be an ImmutableGraphRecord instance."
            )

        if not isinstance(self.metadata, GraphSnapshotMetadata):
            raise GraphValidationError(
                "metadata must be a GraphSnapshotMetadata instance."
            )

        expected_digest = canonical_graph_record_digest(self.record)

        if self.identity.content_digest != expected_digest:
            raise GraphValidationError(
                "Snapshot content_digest does not match record content."
            )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "identity": {
                "snapshot_id": self.identity.snapshot_id,
                "content_digest": self.identity.content_digest,
                "sequence_number": self.identity.sequence_number,
            },
            "record": graph_record_to_mapping(self.record),
            "metadata": self.metadata.to_mapping(),
        }


def snapshots_are_equivalent(
    left: GraphSnapshot,
    right: GraphSnapshot,
) -> bool:
    """Return True when two snapshots have equivalent graph content."""

    return canonical_graph_record_digest(left.record) == (
        canonical_graph_record_digest(right.record)
    )


def create_graph_snapshot(
    record: ImmutableGraphRecord,
    sequence_number: int,
    metadata: GraphSnapshotMetadata | None = None,
) -> GraphSnapshot:
    """Create a validated graph snapshot from a graph record."""

    content_digest = canonical_graph_record_digest(record)

    identity = GraphSnapshotIdentity(
        snapshot_id=build_snapshot_id(sequence_number),
        content_digest=content_digest,
        sequence_number=sequence_number,
    )

    return GraphSnapshot(
        identity=identity,
        record=record,
        metadata=metadata or GraphSnapshotMetadata(),
    )
