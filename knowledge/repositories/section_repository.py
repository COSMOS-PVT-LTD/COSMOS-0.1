"""Section repository facade."""

from __future__ import annotations

from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.models.section import Section
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("SectionRepository",)


class SectionRepository(KnowledgeRepository[Section]):
    def __init__(self) -> None:
        super().__init__(
            id_of=lambda item: item.node_id,
            lifecycle_of=lambda _item: KnowledgeLifecycle.APPROVED,
        )
