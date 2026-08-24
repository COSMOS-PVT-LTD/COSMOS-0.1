"""Entity embeddings as a retrieval aid — never the authoritative representation."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.embeddings import create_embedding_backend

__all__ = ("EntityEmbedding", "EntityEmbeddingIndex")


@dataclass(frozen=True, slots=True, kw_only=True)
class EntityEmbedding:
    entity_id: str
    entity_type: str
    text: str
    vector: tuple[float, ...]


class EntityEmbeddingIndex:
    """Local embeddings for documents, sections, equations, and entities."""

    def __init__(self, *, backend_name: str = "deterministic") -> None:
        self._backend = create_embedding_backend(backend_name)
        self._items: dict[str, EntityEmbedding] = {}

    def embed(
        self,
        *,
        entity_id: str,
        entity_type: str,
        text: str,
    ) -> EntityEmbedding:
        vector = tuple(float(component) for component in self._backend.embed_document(text))
        item = EntityEmbedding(
            entity_id=entity_id,
            entity_type=entity_type,
            text=text,
            vector=vector,
        )
        self._items[entity_id] = item
        return item

    def search(self, text: str, *, limit: int = 8) -> tuple[tuple[EntityEmbedding, float], ...]:
        query = tuple(float(component) for component in self._backend.embed_query(text))
        scored: list[tuple[EntityEmbedding, float]] = []
        for item in self._items.values():
            scored.append((item, _cosine(query, item.vector)))
        scored.sort(key=lambda pair: (-pair[1], pair[0].entity_id))
        return tuple(scored[:limit])


def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sum(value * value for value in left) ** 0.5
    right_norm = sum(value * value for value in right) ** 0.5
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)
