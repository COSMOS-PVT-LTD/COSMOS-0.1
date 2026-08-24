"""Empirical-relation repository facade."""

from __future__ import annotations

from knowledge.models.empirical_relation import EmpiricalRelation
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("EmpiricalRelationRepository",)


class EmpiricalRelationRepository(KnowledgeRepository[EmpiricalRelation]):
    def __init__(self) -> None:
        super().__init__(
            id_of=lambda item: item.relation_id,
            lifecycle_of=lambda item: item.lifecycle,
        )
