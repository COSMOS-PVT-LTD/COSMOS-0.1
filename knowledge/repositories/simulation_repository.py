"""Simulation repository facade."""

from __future__ import annotations

from knowledge.models.simulation import Simulation
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("SimulationRepository",)


class SimulationRepository(KnowledgeRepository[Simulation]):
    def __init__(self) -> None:
        super().__init__(id_of=lambda item: item.simulation_id, lifecycle_of=lambda item: item.lifecycle)
