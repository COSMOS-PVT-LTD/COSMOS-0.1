"""Experiment repository facade."""

from __future__ import annotations

from knowledge.models.experiment import Experiment
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("ExperimentRepository",)


class ExperimentRepository(KnowledgeRepository[Experiment]):
    def __init__(self) -> None:
        super().__init__(
            id_of=lambda item: item.experiment_id,
            lifecycle_of=lambda item: item.lifecycle,
        )
