"""Engineering-authority ranking — approved knowledge always outranks candidates."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.lifecycle import KnowledgeLifecycle

__all__ = ("AuthorityRankedHit", "rank_by_authority")


@dataclass(frozen=True, slots=True, kw_only=True)
class AuthorityRankedHit:
    entity_id: str
    entity_type: str
    title: str
    snippet: str
    lifecycle: KnowledgeLifecycle
    provenance_id: str | None
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    graph_score: float = 0.0
    source_authority: float = 0.0


def rank_by_authority(hits: tuple[AuthorityRankedHit, ...]) -> tuple[AuthorityRankedHit, ...]:
    """Rank hits so an unapproved item can never outrank an approved item."""

    def sort_key(hit: AuthorityRankedHit) -> tuple[int, float, str]:
        approved = 0 if hit.lifecycle is KnowledgeLifecycle.APPROVED else 1
        combined = (
            0.35 * hit.source_authority
            + 0.25 * hit.keyword_score
            + 0.20 * hit.semantic_score
            + 0.20 * hit.graph_score
        )
        return (approved, -combined, hit.entity_id)

    return tuple(sorted(hits, key=sort_key))
