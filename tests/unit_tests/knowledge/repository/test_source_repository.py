"""Unit tests for knowledge.repository.source_repository."""

from __future__ import annotations

import pytest

from knowledge.graph.source_identity import (
    SourceIdentity,
    SourceStatus,
    SourceType,
)
from knowledge.repository.source_repository import (
    SourceRepository,
    SourceRepositoryError,
)


def test_source_repository_add_and_get_source() -> None:
    """Repository must store and return registered sources."""

    repository = SourceRepository()
    source = SourceIdentity(
        source_id="SRC-010",
        source_type=SourceType.WEBSITE,
        title="Reference Site",
    )

    repository.add_source(source)

    assert repository.get_source("SRC-010") == source
    assert repository.has_source("SRC-010")


def test_source_repository_duplicate_registration_fails() -> None:
    """Duplicate registrations must surface as repository errors."""

    repository = SourceRepository()
    source = SourceIdentity(
        source_id="SRC-011",
        source_type=SourceType.DATASET,
        title="Dataset",
    )

    repository.add_source(source)

    with pytest.raises(SourceRepositoryError):
        repository.add_source(source)


def test_source_repository_missing_source_fails() -> None:
    """Missing source lookups must surface as repository errors."""

    repository = SourceRepository()

    with pytest.raises(SourceRepositoryError):
        repository.get_source("missing")


def test_source_repository_update_status() -> None:
    """Repository status updates must delegate to the registry."""

    repository = SourceRepository()
    repository.add_source(
        SourceIdentity(
            source_id="SRC-012",
            source_type=SourceType.INTERNAL_DOCUMENT,
            title="Internal Note",
        ),
    )

    updated = repository.update_source_status(
        "SRC-012",
        SourceStatus.INGESTED,
    )

    assert updated.source_status is SourceStatus.INGESTED
