"""Unified search pipeline: classify → retrieve → rank → evidence → provenance."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.foundation.authority_ranker import AuthorityRankedHit, rank_by_authority
from knowledge.foundation.entity_embeddings import EntityEmbeddingIndex
from knowledge.foundation.keyword_index import KeywordIndex
from knowledge.foundation.query_classification import QueryKind, classify_query
from knowledge.foundation.rag_policy import KnowledgePolicy, apply_knowledge_policy
from knowledge.graph.concept_graph import ConceptGraph
from knowledge.indexing.citation_index import CitationIndex
from knowledge.indexing.equation_index import EquationIndex
from knowledge.indexing.variable_index import VariableIndex
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.search.citation_search import search_citations
from knowledge.search.equation_search import search_equations
from knowledge.search.variable_search import search_variables

__all__ = ("UnifiedSearchPipeline", "UnifiedSearchResult")


@dataclass(frozen=True, slots=True, kw_only=True)
class UnifiedSearchResult:
    query: str
    kind: QueryKind
    hits: tuple[AuthorityRankedHit, ...]
    evidence: tuple[str, ...]
    provenance_ids: tuple[str, ...]


class UnifiedSearchPipeline:
    def __init__(
        self,
        *,
        keywords: KeywordIndex,
        equations: EquationIndex,
        variables: VariableIndex,
        citations: CitationIndex,
        embeddings: EntityEmbeddingIndex | None = None,
        graph: ConceptGraph | None = None,
        policy: KnowledgePolicy | None = None,
    ) -> None:
        self._keywords = keywords
        self._equations = equations
        self._variables = variables
        self._citations = citations
        self._embeddings = embeddings
        self._graph = graph
        self._policy = policy or KnowledgePolicy()

    def search(self, query: str) -> UnifiedSearchResult:
        kind = classify_query(query)
        collected: dict[str, AuthorityRankedHit] = {}

        for keyword_hit in self._keywords.search(query):
            collected[keyword_hit.entity_id] = AuthorityRankedHit(
                entity_id=keyword_hit.entity_id,
                entity_type=keyword_hit.entity_type,
                title=keyword_hit.title,
                snippet=keyword_hit.title,
                lifecycle=keyword_hit.lifecycle,
                provenance_id=keyword_hit.provenance_id,
                keyword_score=keyword_hit.score,
                source_authority=1.0 if keyword_hit.lifecycle is KnowledgeLifecycle.APPROVED else 0.2,
            )

        if kind in {QueryKind.EQUATION, QueryKind.MIXED, QueryKind.KEYWORD}:
            for equation_entry in search_equations(self._equations, query):
                collected.setdefault(
                    equation_entry.equation_id,
                    AuthorityRankedHit(
                        entity_id=equation_entry.equation_id,
                        entity_type="Equation",
                        title=equation_entry.name,
                        snippet=equation_entry.expression,
                        lifecycle=(
                            KnowledgeLifecycle.APPROVED
                            if equation_entry.status == "APPROVED"
                            else KnowledgeLifecycle.CANDIDATE
                        ),
                        provenance_id=equation_entry.source_document_id,
                        keyword_score=1.0,
                        source_authority=1.0 if equation_entry.status == "APPROVED" else 0.2,
                    ),
                )

        if kind in {QueryKind.VARIABLE, QueryKind.MIXED}:
            for variable_entry in search_variables(self._variables, query):
                collected.setdefault(
                    variable_entry.variable_id,
                    AuthorityRankedHit(
                        entity_id=variable_entry.variable_id,
                        entity_type="Variable",
                        title=variable_entry.name,
                        snippet=variable_entry.symbol,
                        lifecycle=KnowledgeLifecycle.APPROVED,
                        provenance_id=None,
                        keyword_score=1.0,
                        source_authority=0.8,
                    ),
                )

        if kind in {QueryKind.CITATION, QueryKind.MIXED}:
            for citation_entry in search_citations(self._citations, query):
                collected.setdefault(
                    citation_entry.entity_id,
                    AuthorityRankedHit(
                        entity_id=citation_entry.entity_id,
                        entity_type=citation_entry.entity_type,
                        title=citation_entry.entity_id,
                        snippet=citation_entry.reference_id,
                        lifecycle=KnowledgeLifecycle.APPROVED,
                        provenance_id=citation_entry.reference_id,
                        keyword_score=1.0,
                        source_authority=1.0,
                    ),
                )

        if self._embeddings is not None:
            for item, score in self._embeddings.search(query, limit=8):
                existing = collected.get(item.entity_id)
                if existing is None:
                    collected[item.entity_id] = AuthorityRankedHit(
                        entity_id=item.entity_id,
                        entity_type=item.entity_type,
                        title=item.text[:80],
                        snippet=item.text[:160],
                        lifecycle=KnowledgeLifecycle.CANDIDATE,
                        provenance_id=None,
                        semantic_score=score,
                    )
                else:
                    collected[item.entity_id] = AuthorityRankedHit(
                        entity_id=existing.entity_id,
                        entity_type=existing.entity_type,
                        title=existing.title,
                        snippet=existing.snippet,
                        lifecycle=existing.lifecycle,
                        provenance_id=existing.provenance_id,
                        keyword_score=existing.keyword_score,
                        semantic_score=score,
                        graph_score=existing.graph_score,
                        source_authority=existing.source_authority,
                    )

        if self._graph is not None:
            for entity_id, hit in list(collected.items()):
                related = self._graph.neighbors(entity_id)
                if not related:
                    continue
                collected[entity_id] = AuthorityRankedHit(
                    entity_id=hit.entity_id,
                    entity_type=hit.entity_type,
                    title=hit.title,
                    snippet=hit.snippet,
                    lifecycle=hit.lifecycle,
                    provenance_id=hit.provenance_id,
                    keyword_score=hit.keyword_score,
                    semantic_score=hit.semantic_score,
                    graph_score=min(1.0, 0.15 * len(related)),
                    source_authority=hit.source_authority,
                )

        ranked = apply_knowledge_policy(rank_by_authority(tuple(collected.values())), self._policy)
        return UnifiedSearchResult(
            query=query,
            kind=kind,
            hits=ranked,
            evidence=tuple(hit.snippet for hit in ranked),
            provenance_ids=tuple(hit.provenance_id for hit in ranked if hit.provenance_id),
        )
