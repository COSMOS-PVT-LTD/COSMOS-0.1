"""Hybrid neural retrieval integration tests (Step 7 final completion)."""

from __future__ import annotations

from knowledge.graph import GraphQueryService
from knowledge.production.local_rag_pipeline import ProductionLocalRAGPipeline
from knowledge.production.neural_index_builder import build_production_index_bundle
from knowledge.production.retrieval_service import ProductionRetrievalService
from knowledge.search import RetrievalMode


def test_neural_pipeline_ingest_query_offline(tmp_path) -> None:
    pipeline = ProductionLocalRAGPipeline(tmp_path, embedding_mode="neural")
    pipeline.initialize()

    content = (
        "# LOX Propulsion\n\n"
        "Liquid oxygen oxidizer supports bipropellant chamber pressure control."
    )
    pipeline.ingest_document(
        document_id="DOC-NEURAL",
        source_id="SRC-NEURAL",
        artifact_id="ART-NEURAL",
        content=content,
        query_text="liquid oxygen oxidizer",
    )

    result = pipeline.query(
        task="Neural hybrid retrieval",
        query_text="liquid oxygen oxidizer bipropellant",
        document_id="DOC-NEURAL",
        request_id="neural-hybrid-001",
    )

    assert result.provider_invoked is False
    assert result.index_bundle.vector_index.dimension() == 64


def test_hybrid_retrieval_uses_local_embedding_backend(tmp_path) -> None:
    pipeline = ProductionLocalRAGPipeline(tmp_path, embedding_mode="neural")
    pipeline.initialize()
    content = "# Heat Transfer\n\nConvective cooling in nozzle channels.\n"

    pipeline.ingest_document(
        document_id="DOC-HEAT",
        source_id="SRC-HEAT",
        artifact_id="ART-HEAT",
        content=content,
    )

    bundle = build_production_index_bundle(
        pipeline.store.graph_store,
        pipeline.embedding_backend,
    )
    graph_query = GraphQueryService(pipeline.store.graph_store)
    service = ProductionRetrievalService(
        bundle=bundle,
        graph_query=graph_query,
        store=pipeline.store.graph_store,
        embedding_backend=pipeline.embedding_backend,
    )

    hybrid = service.retrieve("convective cooling nozzle", mode=RetrievalMode.HYBRID)
    semantic = service.retrieve("convective cooling nozzle", mode=RetrievalMode.SEMANTIC)

    assert hybrid.diagnostics.query_text == "convective cooling nozzle"
    assert semantic.query_vector_source == "local-embedding-backend"
