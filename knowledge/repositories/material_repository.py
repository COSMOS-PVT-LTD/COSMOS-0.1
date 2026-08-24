"""Material repository facade."""

from __future__ import annotations

from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.models.material import Material
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("MaterialRepository",)


class MaterialRepository(KnowledgeRepository[Material]):
    def __init__(self) -> None:
        super().__init__(
            id_of=lambda item: item.material_id,
            lifecycle_of=lambda _item: KnowledgeLifecycle.APPROVED,
        )
