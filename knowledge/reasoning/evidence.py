"""
COSMOS Knowledge Foundation

Module:
    knowledge.reasoning.evidence

Purpose:
    Deterministic evidence assembly for retrieval results.
"""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.graph.lifecycle import GraphLifecycleState
from knowledge.graph.query import GraphQueryService
from knowledge.graph.exceptions import GraphQueryError
from knowledge.search.contracts import NO_VERIFIED_RESULT, SearchResult
from knowledge.search.exceptions import RankingError, SearchValidationError

__all__ = (
    "EvidenceBundle",
    "EvidenceItem",
    "EvidenceRanker",
    "RankingMetadata",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class RankingMetadata:
    """Explainable ranking metadata for a retrieval result."""

    rank: int
    score: float
    ranking_reason: str
    tie_breaker: str

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "rank": self.rank,
            "score": self.score,
            "ranking_reason": self.ranking_reason,
            "tie_breaker": self.tie_breaker,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceItem:
    """Single evidence item supporting a retrieval result."""

    target_id: str
    target_type: str
    document_id: str | None
    lifecycle_state: str | None
    provenance: dict[str, object]
    ranking: RankingMetadata
    graph_neighbor_ids: tuple[str, ...] = ()

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "target_id": self.target_id,
            "target_type": self.target_type,
            "document_id": self.document_id,
            "lifecycle_state": self.lifecycle_state,
            "provenance": self.provenance,
            "ranking": self.ranking.to_mapping(),
            "graph_neighbor_ids": list(self.graph_neighbor_ids),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceBundle:
    """Deterministic evidence bundle assembled from search results."""

    items: tuple[EvidenceItem, ...]
    has_verified_results: bool

    @property
    def has_retrieval_results(self) -> bool:
        """Return True when retrieval produced one or more evidence items."""

        return bool(self.items)

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "items": [item.to_mapping() for item in self.items],
            "has_retrieval_results": self.has_retrieval_results,
            "has_verified_results": self.has_verified_results,
            "no_verified_result": (
                None if self.has_verified_results else NO_VERIFIED_RESULT
            ),
        }


class EvidenceRanker:
    """Assemble deterministic evidence bundles from search results."""

    def __init__(self, graph_query: GraphQueryService) -> None:
        self._graph_query = graph_query

    def assemble(
        self,
        results: tuple[SearchResult, ...],
    ) -> EvidenceBundle:
        """Assemble evidence for ranked search results."""

        if not isinstance(results, tuple):
            raise SearchValidationError("results must be a tuple.")

        if not results:
            return EvidenceBundle(items=(), has_verified_results=False)

        ranked = sorted(
            results,
            key=lambda item: (-item.score, item.target_id),
        )

        items: list[EvidenceItem] = []

        for rank, result in enumerate(ranked, start=1):
            try:
                provenance = self._graph_query.provenance_metadata(
                    result.target_id,
                )
            except GraphQueryError as exc:
                raise RankingError(
                    "Evidence assembly failed to retrieve provenance."
                ) from exc

            neighbors = tuple(
                sorted(
                    neighbor.node_id
                    for neighbor in self._graph_query.neighbors(
                        result.target_id,
                    )
                )
            )

            items.append(
                EvidenceItem(
                    target_id=result.target_id,
                    target_type=result.target_type,
                    document_id=result.document_id,
                    lifecycle_state=result.lifecycle_state,
                    provenance=provenance,
                    ranking=RankingMetadata(
                        rank=rank,
                        score=result.score,
                        ranking_reason=result.ranking_reason or "unspecified",
                        tie_breaker=result.target_id,
                    ),
                    graph_neighbor_ids=neighbors,
                )
            )

        has_verified_results = any(
            item.lifecycle_state == GraphLifecycleState.APPROVED.value
            for item in items
        )

        return EvidenceBundle(
            items=tuple(items),
            has_verified_results=has_verified_results,
        )
