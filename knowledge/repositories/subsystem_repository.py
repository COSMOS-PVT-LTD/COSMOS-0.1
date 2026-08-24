"""Subsystem repository facade."""

from __future__ import annotations

from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.models.subsystem import Subsystem
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("SubsystemRepository",)


class SubsystemRepository(KnowledgeRepository[Subsystem]):
    def __init__(self) -> None:
        super().__init__(
            id_of=lambda item: item.subsystem_id,
            lifecycle_of=lambda _item: KnowledgeLifecycle.APPROVED,
        )
