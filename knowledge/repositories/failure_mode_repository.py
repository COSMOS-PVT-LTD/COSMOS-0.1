"""Failure-mode repository facade."""

from __future__ import annotations

from knowledge.models.failure_mode import FailureMode
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("FailureModeRepository",)


class FailureModeRepository(KnowledgeRepository[FailureMode]):
    def __init__(self) -> None:
        super().__init__(
            id_of=lambda item: item.failure_mode_id,
            lifecycle_of=lambda item: item.lifecycle,
        )
