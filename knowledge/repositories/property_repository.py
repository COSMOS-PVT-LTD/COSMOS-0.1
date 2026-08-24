"""Property repository facade."""

from __future__ import annotations

from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.models.property import PropertyDefinition, PropertyValue
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("PropertyRepository",)


class PropertyRepository:
    """Holds property definitions and sourced values."""

    def __init__(self) -> None:
        self.definitions = KnowledgeRepository[PropertyDefinition](
            id_of=lambda item: item.property_id,
            lifecycle_of=lambda _item: KnowledgeLifecycle.APPROVED,
        )
        self.values = KnowledgeRepository[PropertyValue](
            id_of=lambda item: item.value_id,
            lifecycle_of=lambda item: item.lifecycle,
        )
