"""
COSMOS Knowledge Foundation

Module:
    knowledge.repository.source_repository

Purpose:
    Repository facade for registered knowledge sources.
"""

from __future__ import annotations

from collections.abc import Sequence

from knowledge.graph.source_identity import SourceIdentity, SourceStatus
from knowledge.repository.source_registry import (
    DuplicateSourceError,
    SourceNotFoundError,
    SourceRegistry,
    SourceRegistryError,
)

__all__ = (
    "SourceRepository",
    "SourceRepositoryError",
)


class SourceRepositoryError(SourceRegistryError):
    """Indicate that a source repository operation failed."""


class SourceRepository:
    """
    Repository wrapper around ``SourceRegistry``.

    Provides a stable API aligned with the existing document repository style
  without duplicating registry logic.
    """

    def __init__(self, registry: SourceRegistry | None = None) -> None:
        self._registry = registry or SourceRegistry()

    def add_source(self, source: SourceIdentity) -> None:
        """Store a source identity in the repository."""

        try:
            self._registry.register(source)
        except DuplicateSourceError as exc:
            raise SourceRepositoryError(str(exc)) from exc

    def get_source(self, source_id: str) -> SourceIdentity:
        """Retrieve a source identity by identifier."""

        try:
            return self._registry.get(source_id)
        except SourceNotFoundError as exc:
            raise SourceRepositoryError(str(exc)) from exc

    def has_source(self, source_id: str) -> bool:
        """Return True when the repository contains the source."""

        return self._registry.contains(source_id)

    def list_sources(self) -> Sequence[SourceIdentity]:
        """Return all repository sources in deterministic order."""

        return self._registry.list_sources()

    def update_source_status(
        self,
        source_id: str,
        status: SourceStatus,
    ) -> SourceIdentity:
        """Update and return a source with a new status."""

        try:
            return self._registry.update_status(source_id, status)
        except SourceNotFoundError as exc:
            raise SourceRepositoryError(str(exc)) from exc
