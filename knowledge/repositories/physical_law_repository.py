"""Physical-law repository facade."""

from __future__ import annotations

from knowledge.models.physical_law import PhysicalLaw
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("PhysicalLawRepository",)


class PhysicalLawRepository(KnowledgeRepository[PhysicalLaw]):
    def __init__(self) -> None:
        super().__init__(id_of=lambda item: item.law_id, lifecycle_of=lambda item: item.lifecycle)
