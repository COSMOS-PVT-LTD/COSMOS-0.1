"""Constant repository facade."""

from __future__ import annotations

from knowledge.models.constant import Constant
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("ConstantRepository",)


class ConstantRepository(KnowledgeRepository[Constant]):
    def __init__(self) -> None:
        super().__init__(
            id_of=lambda item: item.constant_id,
            lifecycle_of=lambda _item: KnowledgeLifecycle.APPROVED,
        )
