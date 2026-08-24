"""Citation graph — documents and entities linked by source references."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.indexing.citation_index import CitationIndex, CitationIndexEntry

__all__ = ("CitationGraph", "CitationEdge")


@dataclass(frozen=True, slots=True, kw_only=True)
class CitationEdge:
    source_reference_id: str
    target_entity_id: str
    target_type: str


class CitationGraph:
    def __init__(self, index: CitationIndex) -> None:
        self._index = index

    def edges_from(self, reference_id: str) -> tuple[CitationEdge, ...]:
        return tuple(
            CitationEdge(
                source_reference_id=entry.reference_id,
                target_entity_id=entry.entity_id,
                target_type=entry.entity_type,
            )
            for entry in self._index.search(reference_id)
        )

    def supports(self, reference_id: str, entity_id: str) -> bool:
        return any(entry.entity_id == entity_id for entry in self._index.search(reference_id))
