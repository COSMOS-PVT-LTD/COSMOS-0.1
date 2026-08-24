"""Correlation repository facade."""

from __future__ import annotations

from knowledge.models.correlation import Correlation
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("CorrelationRepository",)


class CorrelationRepository(KnowledgeRepository[Correlation]):
    def __init__(self) -> None:
        super().__init__(id_of=lambda item: item.correlation_id, lifecycle_of=lambda item: item.lifecycle)
