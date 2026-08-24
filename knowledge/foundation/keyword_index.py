"""Unified keyword index over engineering entities."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.lifecycle import KnowledgeLifecycle

__all__ = ("KeywordHit", "KeywordIndex")


@dataclass(frozen=True, slots=True, kw_only=True)
class KeywordHit:
    entity_id: str
    entity_type: str
    title: str
    terms: tuple[str, ...]
    lifecycle: KnowledgeLifecycle
    provenance_id: str | None
    score: float


class KeywordIndex:
    def __init__(self) -> None:
        self._entries: dict[str, KeywordHit] = {}

    def add(
        self,
        *,
        entity_id: str,
        entity_type: str,
        title: str,
        terms: tuple[str, ...],
        lifecycle: KnowledgeLifecycle,
        provenance_id: str | None,
    ) -> None:
        self._entries[entity_id] = KeywordHit(
            entity_id=entity_id,
            entity_type=entity_type,
            title=title,
            terms=tuple(term.lower() for term in terms),
            lifecycle=lifecycle,
            provenance_id=provenance_id,
            score=0.0,
        )

    def search(self, query: str) -> tuple[KeywordHit, ...]:
        tokens = tuple(token for token in query.lower().split() if token)
        if not tokens:
            return ()
        hits: list[KeywordHit] = []
        for entry in self._entries.values():
            haystack = " ".join((entry.title.lower(), *entry.terms, entry.entity_id.lower()))
            matched = sum(1 for token in tokens if token in haystack)
            if matched == 0:
                continue
            hits.append(
                KeywordHit(
                    entity_id=entry.entity_id,
                    entity_type=entry.entity_type,
                    title=entry.title,
                    terms=entry.terms,
                    lifecycle=entry.lifecycle,
                    provenance_id=entry.provenance_id,
                    score=matched / len(tokens),
                ),
            )
        return tuple(sorted(hits, key=lambda item: (-item.score, item.entity_id)))
