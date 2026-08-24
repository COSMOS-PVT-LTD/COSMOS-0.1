"""Chapter repository facade over canonical document-structure nodes."""

from __future__ import annotations

from knowledge.models.chapter import Chapter
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("ChapterRepository",)


class ChapterRepository(KnowledgeRepository[Chapter]):
    def __init__(self) -> None:
        super().__init__(
            id_of=lambda item: item.node_id,
            lifecycle_of=lambda _item: KnowledgeLifecycle.APPROVED,
        )
