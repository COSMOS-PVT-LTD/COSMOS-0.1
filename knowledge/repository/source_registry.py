"""
COSMOS Knowledge Foundation

Module:
    knowledge.repository.source_registry

Purpose:
    Controlled registry abstraction for knowledge sources.
"""

from __future__ import annotations

from collections.abc import Sequence

from knowledge.graph.source_identity import SourceIdentity, SourceStatus

__all__ = (
    "DuplicateSourceError",
    "SourceNotFoundError",
    "SourceRegistry",
    "SourceRegistryError",
)


class SourceRegistryError(Exception):
    """Base exception for source registry failures."""


class DuplicateSourceError(SourceRegistryError):
    """Indicate that a source identifier is already registered."""


class SourceNotFoundError(SourceRegistryError):
    """Indicate that a requested source identifier is not registered."""


class SourceRegistry:
    """
    In-memory registry for ``SourceIdentity`` records.

    The registry enforces deterministic lookup and duplicate rejection without
    performing ingestion or filesystem access.
    """

    def __init__(self) -> None:
        self._sources: dict[str, SourceIdentity] = {}

    def register(self, source: SourceIdentity) -> None:
        """Register a source identity."""

        if not isinstance(source, SourceIdentity):
            raise SourceRegistryError(
                "source must be a SourceIdentity instance."
            )

        if source.source_id in self._sources:
            raise DuplicateSourceError(
                f"Source '{source.source_id}' is already registered."
            )

        self._sources[source.source_id] = source

    def get(self, source_id: str) -> SourceIdentity:
        """Return a registered source by identifier."""

        try:
            return self._sources[source_id]
        except KeyError as exc:
            raise SourceNotFoundError(
                f"Source '{source_id}' is not registered."
            ) from exc

    def contains(self, source_id: str) -> bool:
        """Return True when a source identifier is registered."""

        return source_id in self._sources

    def list_sources(self) -> Sequence[SourceIdentity]:
        """Return registered sources in deterministic source_id order."""

        return tuple(
            self._sources[source_id]
            for source_id in sorted(self._sources)
        )

    def update_status(
        self,
        source_id: str,
        status: SourceStatus,
    ) -> SourceIdentity:
        """Return an updated source record with a new status."""

        current = self.get(source_id)

        if not isinstance(status, SourceStatus):
            raise SourceRegistryError(
                "status must be a SourceStatus value."
            )

        updated = SourceIdentity(
            source_id=current.source_id,
            source_type=current.source_type,
            title=current.title,
            version=current.version,
            content_hash=current.content_hash,
            file_hash=current.file_hash,
            origin=current.origin,
            license_identifier=current.license_identifier,
            source_status=status,
            lineage_parent_source_id=current.lineage_parent_source_id,
        )

        self._sources[source_id] = updated
        return updated
