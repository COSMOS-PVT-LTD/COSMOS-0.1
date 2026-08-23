"""Incremental ingestion coordinator for production local RAG (Step 7)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.pipelines.extended_pipeline import run_knowledge_pipeline_extended
from knowledge.pipelines.orchestrator import KnowledgePipelineArtifacts
from knowledge.production.graph_merge import DocumentGraphMerger, GraphMergeResult
from knowledge.source.integrity import sha256_text_digest
from knowledge.storage.local_store import IngestionState, LocalKnowledgeStore

__all__ = (
    "IncrementalIngestionCoordinator",
    "IngestionAction",
    "IngestionDecision",
)


class IngestionAction(Enum):
    """Incremental ingestion disposition."""

    PROCESSED = "PROCESSED"
    SKIPPED_UNCHANGED = "SKIPPED_UNCHANGED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True, kw_only=True)
class IngestionDecision:
    """Result of an incremental ingestion decision."""

    action: IngestionAction
    document_id: str
    content_digest: str
    version: int = 1


class IncrementalIngestionCoordinator:
    """Coordinate incremental document ingestion with local persistence."""

    def __init__(self, store: LocalKnowledgeStore) -> None:
        self._store = store
        self._graph_merger = DocumentGraphMerger()

    def ingest_document(
        self,
        *,
        document_id: str,
        source_id: str,
        artifact_id: str,
        content: str,
        task: str = "Production local ingestion",
        query_text: str = "engineering evidence",
        request_id: str | None = None,
    ) -> tuple[IngestionDecision, KnowledgePipelineArtifacts | None]:
        """Ingest a document incrementally, skipping unchanged content."""

        content_digest = sha256_text_digest(content)
        existing = self._store.documents.get(document_id)
        state = self._store.ingestion_state

        if existing is not None and existing.content_digest == content_digest:
            updated_state = IngestionState(
                last_processed_document_id=document_id,
                processed_count=state.processed_count,
                skipped_unchanged_count=state.skipped_unchanged_count + 1,
                failed_count=state.failed_count,
            )
            self._store.save_ingestion_state(updated_state)

            return (
                IngestionDecision(
                    action=IngestionAction.SKIPPED_UNCHANGED,
                    document_id=document_id,
                    content_digest=content_digest,
                    version=existing.version,
                ),
                None,
            )

        try:
            record = self._store.register_document(
                document_id=document_id,
                source_id=source_id,
                artifact_id=artifact_id,
                content=content,
            )
            artifacts = run_knowledge_pipeline_extended(
                content,
                task=task,
                query_text=query_text,
                request_id=request_id or f"prod-ingest-{document_id}",
                source_id=source_id,
                artifact_id=document_id,
            )
            graph_document_id = artifacts.extraction.document_id
            merge_result = self._graph_merger.merge_document(
                self._store.graph_store,
                artifacts.store.snapshot(),
                document_id=graph_document_id,
            )
            if not merge_result.success:
                raise RuntimeError(
                    "Graph merge failed: "
                    + "; ".join(merge_result.cross_document_conflicts),
                )
            self._store.save_graph()

            updated_state = IngestionState(
                last_processed_document_id=document_id,
                processed_count=state.processed_count + 1,
                skipped_unchanged_count=state.skipped_unchanged_count,
                failed_count=state.failed_count,
            )
            self._store.save_ingestion_state(updated_state)

            return (
                IngestionDecision(
                    action=IngestionAction.PROCESSED,
                    document_id=document_id,
                    content_digest=content_digest,
                    version=record.version,
                ),
                artifacts,
            )
        except Exception:
            updated_state = IngestionState(
                last_processed_document_id=document_id,
                processed_count=state.processed_count,
                skipped_unchanged_count=state.skipped_unchanged_count,
                failed_count=state.failed_count + 1,
            )
            self._store.save_ingestion_state(updated_state)

            return (
                IngestionDecision(
                    action=IngestionAction.FAILED,
                    document_id=document_id,
                    content_digest=content_digest,
                    version=existing.version if existing else 1,
                ),
                None,
            )

    def remove_document(self, *, document_id: str) -> GraphMergeResult:
        """Remove a document and its graph content from the store."""

        merge_result = self._graph_merger.remove_document(
            self._store.graph_store,
            document_id=document_id,
        )
        self._store.mark_document_removed(document_id)
        self._store.save_graph()
        return merge_result
