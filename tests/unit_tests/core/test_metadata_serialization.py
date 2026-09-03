"""Unit tests for metadata, serialization, and hashing."""

from __future__ import annotations

from core.hashing import canonical_hash
from core.metadata import ObjectMetadata, ProvenanceRecord
from core.serialization import canonical_json_dumps


def test_metadata_canonical_round_trip() -> None:
    metadata = ObjectMetadata(
        object_id="quantity.chamber_pressure",
        object_type="Quantity",
        source="test",
        assumptions=("steady_state",),
        provenance=ProvenanceRecord(
            source="NIST",
            reference="SP-330",
        ),
    )
    restored = ObjectMetadata.from_canonical_dict(metadata.to_canonical_dict())
    assert restored == metadata


def test_canonical_json_sorted_keys() -> None:
    payload = {"b": 2, "a": 1}
    assert canonical_json_dumps(payload) == '{"a":1,"b":2}'


def test_canonical_hash_deterministic() -> None:
    metadata = ObjectMetadata(
        object_id="test.object",
        object_type="Test",
    )
    first = canonical_hash(metadata)
    second = canonical_hash(metadata.to_canonical_dict())
    assert first == second
    assert len(first) == 64
