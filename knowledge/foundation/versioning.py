"""Immutability / supersede workflow for approved knowledge."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.lifecycle import KnowledgeLifecycle, VersionRecord
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("SupersedeRecord", "supersede_entity")


@dataclass(frozen=True, slots=True, kw_only=True)
class SupersedeRecord:
    previous_id: str
    replacement_id: str
    version: VersionRecord


def supersede_entity(
    repository: KnowledgeRepository[object],
    entity_id: str,
    replacement: object,
    *,
    author: str,
    reason: str,
    entity_version: str,
) -> SupersedeRecord:
    current = repository.get(entity_id)
    lifecycle = repository._lifecycle_of(current)  # noqa: SLF001 — typed facade uses shared store
    if lifecycle is KnowledgeLifecycle.APPROVED:
        # Historical record is retained by KnowledgeRepository.supersede.
        pass
    repository.supersede(entity_id, replacement)
    return SupersedeRecord(
        previous_id=entity_id,
        replacement_id=entity_id,
        version=VersionRecord(
            entity_version=entity_version,
            author=author,
            change_reason=reason,
            supersedes_id=entity_id,
        ),
    )
