"""Equation repository facade — no destructive delete of approved equations."""

from __future__ import annotations

from knowledge.models.equation import Equation, EquationStatus
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("EquationRepository",)


def _lifecycle(equation: Equation) -> KnowledgeLifecycle:
    mapping = {
        EquationStatus.DRAFT: KnowledgeLifecycle.CANDIDATE,
        EquationStatus.VERIFIED: KnowledgeLifecycle.REVIEWED,
        EquationStatus.APPROVED: KnowledgeLifecycle.APPROVED,
        EquationStatus.DEPRECATED: KnowledgeLifecycle.DEPRECATED,
    }
    return mapping[equation.status]


class EquationRepository(KnowledgeRepository[Equation]):
    def __init__(self) -> None:
        super().__init__(id_of=lambda item: item.equation_id, lifecycle_of=_lifecycle)
