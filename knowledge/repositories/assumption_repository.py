"""Assumption repository facade."""

from __future__ import annotations

from knowledge.models.assumption import Assumption
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("AssumptionRepository",)


class AssumptionRepository(KnowledgeRepository[Assumption]):
    def __init__(self) -> None:
        super().__init__(
            id_of=lambda item: item.assumption_id,
            lifecycle_of=lambda item: item.lifecycle,
        )
