"""Reference repository facade."""

from __future__ import annotations

from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.models.reference import Reference, ReferenceStatus
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("ReferenceRepository",)


def _lifecycle(reference: Reference) -> KnowledgeLifecycle:
    mapping = {
        ReferenceStatus.DRAFT: KnowledgeLifecycle.CANDIDATE,
        ReferenceStatus.APPROVED: KnowledgeLifecycle.APPROVED,
        ReferenceStatus.DEPRECATED: KnowledgeLifecycle.DEPRECATED,
        ReferenceStatus.ARCHIVED: KnowledgeLifecycle.ARCHIVED,
    }
    return mapping[reference.status]


class ReferenceRepository(KnowledgeRepository[Reference]):
    def __init__(self) -> None:
        super().__init__(id_of=lambda item: item.reference_id, lifecycle_of=_lifecycle)
