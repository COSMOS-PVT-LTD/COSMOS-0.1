"""Unit tests for knowledge.repository.source_registry."""

from __future__ import annotations

import pytest

from knowledge.graph.source_identity import (
    SourceIdentity,
    SourceStatus,
    SourceType,
)
from knowledge.repository.source_registry import (
    DuplicateSourceError,
    SourceNotFoundError,
    SourceRegistry,
)


def test_source_registry_register_and_lookup() -> None:
    """Registered sources must be retrievable by identifier."""

    registry = SourceRegistry()
    source = SourceIdentity(
        source_id="SRC-001",
        source_type=SourceType.PDF,
        title="Propulsion Manual",
    )

    registry.register(source)

    assert registry.get("SRC-001") == source
    assert registry.contains("SRC-001")


def test_duplicate_source_registration_is_rejected() -> None:
    """Duplicate source identifiers must be rejected."""

    registry = SourceRegistry()
    source = SourceIdentity(
        source_id="SRC-002",
        source_type=SourceType.BOOK,
        title="Thermodynamics",
    )

    registry.register(source)

    with pytest.raises(DuplicateSourceError):
        registry.register(source)


def test_missing_source_lookup_is_rejected() -> None:
    """Missing source identifiers must raise SourceNotFoundError."""

    registry = SourceRegistry()

    with pytest.raises(SourceNotFoundError):
        registry.get("missing")


def test_source_registry_lists_sources_deterministically() -> None:
    """Source listing must be deterministic."""

    registry = SourceRegistry()
    second = SourceIdentity(
        source_id="SRC-B",
        source_type=SourceType.STANDARD,
        title="B",
    )
    first = SourceIdentity(
        source_id="SRC-A",
        source_type=SourceType.MANUAL,
        title="A",
    )

    registry.register(second)
    registry.register(first)

    assert [source.source_id for source in registry.list_sources()] == [
        "SRC-A",
        "SRC-B",
    ]


def test_source_registry_update_status_returns_new_record() -> None:
    """Status updates must return an updated immutable source record."""

    registry = SourceRegistry()
    registry.register(
        SourceIdentity(
            source_id="SRC-003",
            source_type=SourceType.JOURNAL,
            title="Paper",
        ),
    )

    updated = registry.update_status("SRC-003", SourceStatus.VERIFIED)

    assert updated.source_status is SourceStatus.VERIFIED
    assert registry.get("SRC-003").source_status is SourceStatus.VERIFIED
