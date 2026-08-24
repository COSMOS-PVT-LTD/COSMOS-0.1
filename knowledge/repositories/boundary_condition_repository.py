"""Boundary-condition repository facade."""

from __future__ import annotations

from knowledge.models.boundary_condition import BoundaryCondition
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("BoundaryConditionRepository",)


class BoundaryConditionRepository(KnowledgeRepository[BoundaryCondition]):
    def __init__(self) -> None:
        super().__init__(
            id_of=lambda item: item.boundary_condition_id,
            lifecycle_of=lambda item: item.lifecycle,
        )
