"""Component repository facade."""

from __future__ import annotations

from knowledge.models.component import Component
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("ComponentRepository",)


class ComponentRepository(KnowledgeRepository[Component]):
    def __init__(self) -> None:
        super().__init__(id_of=lambda item: item.component_id, lifecycle_of=lambda item: item.lifecycle)
