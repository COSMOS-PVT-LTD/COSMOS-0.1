"""Process repository facade."""

from __future__ import annotations

from knowledge.models.process import Process
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("ProcessRepository",)


class ProcessRepository(KnowledgeRepository[Process]):
    def __init__(self) -> None:
        super().__init__(id_of=lambda item: item.process_id, lifecycle_of=lambda item: item.lifecycle)
