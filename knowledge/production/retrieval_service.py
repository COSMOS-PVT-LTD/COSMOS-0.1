"""Production retrieval service with local embeddings (Step 7)."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.embeddings.protocol import EmbeddingBackend
from knowledge.graph.query import GraphQueryService
from knowledge.graph.repository import GraphStore
from knowledge.indexing.w7.bundle import W7IndexBundle
from knowledge.indexing.w7.vector import deterministic_reference_vector
from knowledge.search import RetrievalMode, SearchQuery
from knowledge.search.retrieval_diagnostics import RetrievalDiagnostics, build_retrieval_diagnostics
from knowledge.search.w8.hybrid import HybridSearchEngine
from knowledge.search.w8.semantic import SemanticVectorSearchEngine

__all__ = (
    "ProductionRetrievalResult",
    "ProductionRetrievalService",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProductionRetrievalResult:
    """Production retrieval output with diagnostics."""

    diagnostics: RetrievalDiagnostics
    query_vector_source: str


class ProductionRetrievalService:
    """Production retrieval combining hybrid search and local query embeddings."""

    def __init__(
        self,
        *,
        bundle: W7IndexBundle,
        graph_query: GraphQueryService,
        store: GraphStore,
        embedding_backend: EmbeddingBackend | None = None,
    ) -> None:
        self._bundle = bundle
        self._graph_query = graph_query
        self._store = store
        from knowledge.embeddings import create_embedding_backend

        self._embedding_backend = embedding_backend or create_embedding_backend("deterministic")
        self._hybrid = HybridSearchEngine(bundle, graph_query, store)

    def retrieve(
        self,
        query_text: str,
        *,
        mode: RetrievalMode = RetrievalMode.HYBRID,
    ) -> ProductionRetrievalResult:
        """Execute production retrieval with deterministic local query embedding."""

        query = SearchQuery(text=query_text, mode=mode)
        page = self._hybrid.search(query)
        diagnostics = build_retrieval_diagnostics(query, page)

        if mode is RetrievalMode.SEMANTIC:
            query_vector = self._embedding_backend.embed_query(query_text)
            semantic_engine = SemanticVectorSearchEngine(
                self._bundle.vector_index,
                source_digest=self._bundle.source_digest,
                store=self._store,
            )
            page = semantic_engine.search(query, query_vector=query_vector)
            diagnostics = build_retrieval_diagnostics(query, page)
            vector_source = "local-embedding-backend"
        else:
            vector_source = "hybrid-default"

        return ProductionRetrievalResult(
            diagnostics=diagnostics,
            query_vector_source=vector_source,
        )

    def build_query_vector_for_target(self, target_id: str) -> tuple[float, ...]:
        """Build a compatible query vector for semantic retrieval tests."""

        return deterministic_reference_vector(
            target_id=target_id,
            dimension=self._bundle.vector_index.dimension(),
        )
