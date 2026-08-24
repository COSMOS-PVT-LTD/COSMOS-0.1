"""Controlled RAG policy — AI cannot retrieve arbitrary unapproved text."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.foundation.authority_ranker import AuthorityRankedHit, rank_by_authority
from knowledge.models.lifecycle import KnowledgeLifecycle

__all__ = ("KnowledgePolicy", "apply_knowledge_policy")


@dataclass(frozen=True, slots=True, kw_only=True)
class KnowledgePolicy:
    require_approved: bool = True
    require_provenance: bool = True
    allow_unknown_source: bool = False
    max_results: int = 8


def apply_knowledge_policy(
    hits: tuple[AuthorityRankedHit, ...],
    policy: KnowledgePolicy | None = None,
) -> tuple[AuthorityRankedHit, ...]:
    policy = policy or KnowledgePolicy()
    filtered: list[AuthorityRankedHit] = []
    for hit in rank_by_authority(hits):
        if policy.require_approved and hit.lifecycle is not KnowledgeLifecycle.APPROVED:
            continue
        if policy.require_provenance and not hit.provenance_id:
            continue
        if not policy.allow_unknown_source and hit.provenance_id in {None, "UNKNOWN"}:
            continue
        filtered.append(hit)
        if len(filtered) >= policy.max_results:
            break
    return tuple(filtered)
