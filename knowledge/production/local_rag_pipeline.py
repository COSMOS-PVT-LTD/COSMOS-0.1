"""Production local RAG pipeline orchestration (Step 7)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from knowledge.embeddings import EmbeddingBackend, create_embedding_backend
from knowledge.graph import GraphQueryService
from knowledge.indexing.w7.bundle import W7IndexBundle
from knowledge.interface import (
    ContextPackager,
    ControlledRAGOrchestrator,
    ControlledRAGRequest,
)
from knowledge.interface.evidence_summary import summarize_evidence
from knowledge.interface.models import ControlledRAGResult
from knowledge.production.incremental_ingestion import (
    IncrementalIngestionCoordinator,
    IngestionAction,
)
from knowledge.production.observability import ObservabilityRecorder, ObservabilityStage
from knowledge.production.offline_guard import OfflineExecutionGuard, ProviderInvocationState
from knowledge.production.recovery import RecoveryProcedure
from knowledge.production.retrieval_service import ProductionRetrievalService
from knowledge.search import RetrievalMode, SearchQuery
from knowledge.storage.index_lifecycle import IndexLifecycleManager
from knowledge.storage.local_store import LocalKnowledgeStore

__all__ = (
    "ProductionLocalRAGPipeline",
    "ProductionLocalRAGResult",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProductionLocalRAGResult:
    """Result from a production local RAG query."""

    rag_result: ControlledRAGResult
    index_bundle: W7IndexBundle
    provider_state: ProviderInvocationState
    retrieval_diagnostics_digest: str
    evidence_summary_digest: str
    store_root: str

    @property
    def provider_invoked(self) -> bool:
        return self.provider_state.provider_invoked


class ProductionLocalRAGPipeline:
    """Persistent local-first controlled RAG pipeline."""

    def __init__(
        self,
        store_root: str | Path,
        *,
        store_id: str = "cosmos-production-local",
        vector_dimension: int | None = None,
        embedding_mode: str = "deterministic",
    ) -> None:
        self._embedding_backend = create_embedding_backend(embedding_mode)
        resolved_dimension = vector_dimension or self._embedding_backend.identity.dimension
        self._store = LocalKnowledgeStore(store_root, store_id=store_id)
        self._index_manager = IndexLifecycleManager(
            indexes_dir=self._store.root_dir / "indexes",
            embedding_model=self._embedding_backend.identity,
            vector_dimension=resolved_dimension,
            embedding_backend=self._embedding_backend,
        )
        self._ingestion = IncrementalIngestionCoordinator(self._store)
        self._recovery = RecoveryProcedure(
            store=self._store,
            index_manager=self._index_manager,
        )
        self._observability = ObservabilityRecorder()
        self._offline_guard = OfflineExecutionGuard()

    @property
    def observability(self) -> ObservabilityRecorder:
        return self._observability

    @property
    def store(self) -> LocalKnowledgeStore:
        return self._store

    @property
    def embedding_backend(self) -> EmbeddingBackend:
        return self._embedding_backend

    def initialize(self) -> None:
        """Initialize or load the local knowledge store."""

        with self._observability.timed(
            stage=ObservabilityStage.RECOVERY,
            operation="initialize_store",
        ):
            self._store.load()

    def ingest_document(
        self,
        *,
        document_id: str,
        source_id: str,
        artifact_id: str,
        content: str,
        query_text: str = "engineering evidence",
    ) -> IngestionAction:
        """Incrementally ingest a document and rebuild indexes when changed."""

        with self._observability.timed(
            stage=ObservabilityStage.INGESTION,
            operation="ingest_document",
            metadata={"document_id": document_id},
        ):
            decision, artifacts = self._ingestion.ingest_document(
                document_id=document_id,
                source_id=source_id,
                artifact_id=artifact_id,
                content=content,
                query_text=query_text,
                request_id=f"prod-{document_id}",
            )

        if decision.action is IngestionAction.PROCESSED and artifacts is not None:
            with self._observability.timed(
                stage=ObservabilityStage.INDEXING,
                operation="build_indexes",
                metadata={"document_id": document_id},
            ):
                self._index_manager.rebuild(self._store.graph_store)

        return decision.action

    def query(
        self,
        *,
        task: str,
        query_text: str,
        document_id: str,
        request_id: str = "production-local-rag",
    ) -> ProductionLocalRAGResult:
        """Execute a production local controlled RAG query."""

        offline_report = self._offline_guard.verify_environment()

        with self._observability.timed(
            stage=ObservabilityStage.RETRIEVAL,
            operation="load_indexes",
        ):
            index_bundle = self._index_manager.load(self._store.graph_store)

        store = self._store.graph_store
        graph_query = GraphQueryService(store)
        query = SearchQuery(text=query_text, mode=RetrievalMode.HYBRID)

        retrieval_service = ProductionRetrievalService(
            bundle=index_bundle,
            graph_query=graph_query,
            store=store,
            embedding_backend=self._embedding_backend,
        )

        with self._observability.timed(
            stage=ObservabilityStage.RAG,
            operation="controlled_rag_retrieve",
            metadata={"request_id": request_id},
        ):
            rag_orchestrator = ControlledRAGOrchestrator(
                index_bundle=index_bundle,
                graph_query=graph_query,
                store=store,
            )
            rag_result = rag_orchestrator.retrieve(
                ControlledRAGRequest(
                    request_id=request_id,
                    task=task,
                    query=query,
                    allowed_document_ids=(document_id,),
                ),
            )

        retrieval = retrieval_service.retrieve(query_text)
        package = ContextPackager().package(rag_result)
        summary = summarize_evidence(package)

        provider_state = ProviderInvocationState(
            provider_invoked=rag_result.provider_invoked,
        )

        assert provider_state.provider_invoked is False
        assert offline_report.provider_state.provider_invoked is False

        return ProductionLocalRAGResult(
            rag_result=rag_result,
            index_bundle=index_bundle,
            provider_state=provider_state,
            retrieval_diagnostics_digest=retrieval.diagnostics.report_digest,
            evidence_summary_digest=summary.summary_digest,
            store_root=str(self._store.root_dir),
        )

    def recover(self) -> None:
        """Execute recovery procedures after failures."""

        with self._observability.timed(
            stage=ObservabilityStage.RECOVERY,
            operation="recover",
        ):
            self._recovery.recover()
