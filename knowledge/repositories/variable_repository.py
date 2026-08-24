"""Variable repository facade."""

from __future__ import annotations

from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.models.variable import Variable
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("VariableRepository",)


class VariableRepository(KnowledgeRepository[Variable]):
    def __init__(self) -> None:
        super().__init__(
            id_of=lambda item: item.variable_id,
            lifecycle_of=lambda _item: KnowledgeLifecycle.APPROVED,
        )
