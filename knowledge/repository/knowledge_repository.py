"""Generic knowledge repository — create/read/supersede/archive, never destructive delete."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

from knowledge.models.lifecycle import KnowledgeLifecycle

__all__ = (
    "DestructiveDeleteError",
    "EntityNotFoundError",
    "KnowledgeRepository",
    "KnowledgeRepositoryError",
)


class KnowledgeRepositoryError(Exception):
    """Repository operation failed."""


class EntityNotFoundError(KnowledgeRepositoryError):
    """Requested entity is not in the repository."""


class DestructiveDeleteError(KnowledgeRepositoryError):
    """Approved engineering knowledge cannot be destructively deleted."""


T = TypeVar("T")


class KnowledgeRepository(Generic[T]):
    """In-memory typed repository with lifecycle-safe mutations."""

    def __init__(self, *, id_of: Callable[[T], str], lifecycle_of: Callable[[T], KnowledgeLifecycle]) -> None:
        self._id_of = id_of
        self._lifecycle_of = lifecycle_of
        self._entities: dict[str, T] = {}
        self._history: dict[str, list[T]] = {}

    def create(self, entity: T) -> T:
        entity_id = self._id_of(entity)
        if entity_id in self._entities:
            raise KnowledgeRepositoryError(f"Entity '{entity_id}' already exists.")
        self._entities[entity_id] = entity
        self._history.setdefault(entity_id, []).append(entity)
        return entity

    def get(self, entity_id: str) -> T:
        if entity_id not in self._entities:
            raise EntityNotFoundError(f"Entity '{entity_id}' was not found.")
        return self._entities[entity_id]

    def query(self, predicate: Callable[[T], bool] | None = None) -> tuple[T, ...]:
        values = tuple(self._entities[key] for key in sorted(self._entities))
        if predicate is None:
            return values
        return tuple(item for item in values if predicate(item))

    def supersede(self, entity_id: str, replacement: T) -> T:
        current = self.get(entity_id)
        self._history.setdefault(entity_id, []).append(current)
        self._entities[entity_id] = replacement
        self._history[entity_id].append(replacement)
        return replacement

    def archive(self, entity_id: str) -> T:
        return self.get(entity_id)

    def history(self, entity_id: str) -> tuple[T, ...]:
        if entity_id not in self._history:
            raise EntityNotFoundError(f"Entity '{entity_id}' has no history.")
        return tuple(self._history[entity_id])

    def delete(self, entity_id: str) -> None:
        entity = self.get(entity_id)
        lifecycle = self._lifecycle_of(entity)
        if lifecycle in {
            KnowledgeLifecycle.APPROVED,
            KnowledgeLifecycle.DEPRECATED,
            KnowledgeLifecycle.ARCHIVED,
            KnowledgeLifecycle.SUPERSEDED,
        }:
            raise DestructiveDeleteError(
                "Approved or historically retained knowledge cannot be deleted; "
                "archive or supersede it instead.",
            )
        if lifecycle is KnowledgeLifecycle.CANDIDATE:
            del self._entities[entity_id]
            return
        raise DestructiveDeleteError(
            f"Cannot delete entity in lifecycle '{lifecycle.value}'.",
        )
