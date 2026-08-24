"""Manufacturing-process repository facade."""

from __future__ import annotations

from knowledge.models.manufacturing_process import ManufacturingProcess
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("ManufacturingProcessRepository",)


class ManufacturingProcessRepository(KnowledgeRepository[ManufacturingProcess]):
    def __init__(self) -> None:
        super().__init__(id_of=lambda item: item.process_id, lifecycle_of=lambda item: item.lifecycle)
