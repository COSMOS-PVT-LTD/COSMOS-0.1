"""Citation search over the citation index."""

from __future__ import annotations

from knowledge.indexing.citation_index import CitationIndex, CitationIndexEntry

__all__ = ("search_citations",)


def search_citations(index: CitationIndex, reference_id: str) -> tuple[CitationIndexEntry, ...]:
    return index.search(reference_id)
