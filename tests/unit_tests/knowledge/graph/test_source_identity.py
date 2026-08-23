"""Unit tests for knowledge.graph.source_identity."""

from __future__ import annotations

import pytest

from knowledge.graph import GraphValidationError
from knowledge.graph.source_identity import (
    ArtifactIdentity,
    SourceIdentity,
    SourceStatus,
    SourceType,
    is_valid_sha256_hex,
)

_VALID_SHA256 = "a" * 64


def test_source_identity_is_deterministic() -> None:
    """Repeated construction with identical inputs must be equal."""

    first = SourceIdentity(
        source_id="SRC-001",
        source_type=SourceType.PDF,
        title="Rocket Propulsion Elements",
        version="3rd-edition",
    )
    second = SourceIdentity(
        source_id="SRC-001",
        source_type=SourceType.PDF,
        title="Rocket Propulsion Elements",
        version="3rd-edition",
    )

    assert first == second
    assert first.identity_key() == second.identity_key()
    assert hash(first) == hash(second)


def test_source_identity_supports_hashes_and_lineage() -> None:
    """Source identity must retain hash and lineage metadata."""

    source = SourceIdentity(
        source_id="SRC-002",
        source_type=SourceType.STANDARD,
        title="NASA Standard",
        content_hash=_VALID_SHA256,
        file_hash=_VALID_SHA256,
        lineage_parent_source_id="SRC-001",
    )

    assert source.content_hash == _VALID_SHA256.lower()
    assert source.lineage_parent_source_id == "SRC-001"


def test_source_identity_rejects_blank_source_id() -> None:
    """Blank source identifiers must be rejected."""

    with pytest.raises(GraphValidationError):
        SourceIdentity(
            source_id="   ",
            source_type=SourceType.BOOK,
            title="Title",
        )


def test_source_identity_rejects_invalid_content_hash() -> None:
    """Invalid SHA-256 digests must be rejected."""

    with pytest.raises(GraphValidationError):
        SourceIdentity(
            source_id="SRC-003",
            source_type=SourceType.DATASET,
            title="Dataset",
            content_hash="not-a-hash",
        )


def test_source_type_discrimination() -> None:
    """Different source types must remain distinct."""

    pdf = SourceIdentity(
        source_id="SRC-004",
        source_type=SourceType.PDF,
        title="Same Title",
    )
    book = SourceIdentity(
        source_id="SRC-004",
        source_type=SourceType.BOOK,
        title="Same Title",
    )

    assert pdf != book


def test_artifact_identity_is_deterministic() -> None:
    """Artifact identity must be deterministic."""

    first = ArtifactIdentity(
        artifact_id="ART-001",
        source_id="SRC-001",
        artifact_type="document",
        version="v1",
    )
    second = ArtifactIdentity(
        artifact_id="ART-001",
        source_id="SRC-001",
        artifact_type="document",
        version="v1",
    )

    assert first == second
    assert first.identity_key() == second.identity_key()


def test_artifact_identity_rejects_blank_artifact_type() -> None:
    """Artifact type must be a non-blank string."""

    with pytest.raises(GraphValidationError):
        ArtifactIdentity(
            artifact_id="ART-002",
            source_id="SRC-001",
            artifact_type="",
        )


def test_is_valid_sha256_hex() -> None:
    """SHA-256 helper must accept only 64-character hex digests."""

    assert is_valid_sha256_hex(_VALID_SHA256)
    assert not is_valid_sha256_hex("abc")
    assert not is_valid_sha256_hex("g" * 64)


def test_source_identity_mapping_round_trip_fields() -> None:
    """Serialization mapping must preserve identity fields."""

    source = SourceIdentity(
        source_id="SRC-005",
        source_type=SourceType.MANUAL,
        title="Operations Manual",
        version="rev-a",
        source_status=SourceStatus.VERIFIED,
    )

    mapping = source.to_mapping()

    assert mapping["source_id"] == "SRC-005"
    assert mapping["source_type"] == "MANUAL"
    assert mapping["source_status"] == "VERIFIED"
