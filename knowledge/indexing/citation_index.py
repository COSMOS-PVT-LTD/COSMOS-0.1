"""Citation index — what knowledge came from a given source."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

__all__ = ("CitationIndex", "CitationIndexEntry")


@dataclass(frozen=True, slots=True, kw_only=True)
class CitationIndexEntry:
    reference_id: str
    entity_id: str
    entity_type: str
    document_id: str | None = None
    page: int | None = None


class CitationIndex:
    def __init__(self) -> None:
        self._by_reference: dict[str, list[CitationIndexEntry]] = defaultdict(list)

    def add(self, entry: CitationIndexEntry) -> None:
        self._by_reference[entry.reference_id].append(entry)

    def search(self, reference_id: str) -> tuple[CitationIndexEntry, ...]:
        return tuple(self._by_reference.get(reference_id.strip(), ()))
