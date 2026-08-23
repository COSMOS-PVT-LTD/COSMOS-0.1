"""Step 7 production local RAG pipeline tests."""

from __future__ import annotations

from pathlib import Path

from knowledge.production import (
    IngestionAction,
    ProductionLocalRAGPipeline,
)
from knowledge.production.incremental_ingestion import IncrementalIngestionCoordinator
from knowledge.storage import LocalKnowledgeStore

_GOLDEN_DOCUMENT = (
    Path(__file__).resolve().parents[3]
    / "integration_tests"
    / "kg_block012"
    / "fixtures"
    / "documents"
    / "golden_propulsion_spec.md"
)


def test_production_pipeline_ingest_and_query(tmp_path) -> None:
    """Production pipeline must ingest, persist, and query locally."""

    content = _GOLDEN_DOCUMENT.read_text(encoding="utf-8")
    pipeline = ProductionLocalRAGPipeline(tmp_path)
    pipeline.initialize()

    action = pipeline.ingest_document(
        document_id="DOC-GOLDEN",
        source_id="SRC-GOLDEN",
        artifact_id="ART-GOLDEN",
        content=content,
        query_text="chamber pressure LOX",
    )

    assert action is IngestionAction.PROCESSED

    result = pipeline.query(
        task="Production qualification",
        query_text="chamber pressure LOX",
        document_id="DOC-GOLDEN",
    )

    assert result.provider_invoked is False
    assert result.rag_result.provider_invoked is False
    assert result.retrieval_diagnostics_digest


def test_incremental_ingestion_skips_unchanged_document(tmp_path) -> None:
    """Incremental ingestion must skip unchanged documents."""

    store = LocalKnowledgeStore(tmp_path)
    store.initialize()
    coordinator = IncrementalIngestionCoordinator(store)
    content = "# Spec\n\nChamber pressure nominal.\n"

    first, _ = coordinator.ingest_document(
        document_id="DOC-001",
        source_id="SRC-001",
        artifact_id="ART-001",
        content=content,
    )
    second, artifacts = coordinator.ingest_document(
        document_id="DOC-001",
        source_id="SRC-001",
        artifact_id="ART-001",
        content=content,
    )

    assert first.action is IngestionAction.PROCESSED
    assert second.action is IngestionAction.SKIPPED_UNCHANGED
    assert artifacts is None
    assert store.ingestion_state.skipped_unchanged_count == 1


def test_production_pipeline_restart_recovery(tmp_path) -> None:
    """Pipeline must reload persisted state after restart."""

    content = "# Spec\n\nRestart recovery check.\n"
    pipeline = ProductionLocalRAGPipeline(tmp_path)
    pipeline.initialize()
    pipeline.ingest_document(
        document_id="DOC-RESTART",
        source_id="SRC-RESTART",
        artifact_id="ART-RESTART",
        content=content,
    )

    restarted = ProductionLocalRAGPipeline(tmp_path)
    restarted.initialize()
    restarted.recover()

    assert restarted.store.documents["DOC-RESTART"].document_id == "DOC-RESTART"
