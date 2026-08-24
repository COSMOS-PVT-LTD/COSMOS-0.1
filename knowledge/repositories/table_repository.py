"""Table repository facade over W3 parsed tables."""

from __future__ import annotations

from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.parsers.w3.models import ParsedTable
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("TableRepository",)


class TableRepository(KnowledgeRepository[ParsedTable]):
    def __init__(self) -> None:
        super().__init__(
            id_of=lambda item: item.table_id,
            lifecycle_of=lambda _item: KnowledgeLifecycle.APPROVED,
        )
