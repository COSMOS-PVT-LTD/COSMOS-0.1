"""Figure repository facade over W3 parsed figures."""

from __future__ import annotations

from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.parsers.w3.models import ParsedFigure
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("FigureRepository",)


class FigureRepository(KnowledgeRepository[ParsedFigure]):
    def __init__(self) -> None:
        super().__init__(
            id_of=lambda item: item.figure_id,
            lifecycle_of=lambda _item: KnowledgeLifecycle.APPROVED,
        )
