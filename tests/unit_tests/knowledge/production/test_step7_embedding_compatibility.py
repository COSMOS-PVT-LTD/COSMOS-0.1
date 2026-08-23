"""Embedding/index compatibility tests (Step 7 final completion)."""

from __future__ import annotations

import pytest

from knowledge.embeddings import create_embedding_backend
from knowledge.production.local_rag_pipeline import ProductionLocalRAGPipeline
from knowledge.storage.exceptions import SchemaMismatchError
from knowledge.storage.index_lifecycle import IndexLifecycleManager


def test_persisted_index_includes_embedding_configuration_hash(tmp_path) -> None:
    pipeline = ProductionLocalRAGPipeline(tmp_path, embedding_mode="neural")
    pipeline.initialize()
    pipeline.ingest_document(
        document_id="DOC-COMPAT",
        source_id="SRC-COMPAT",
        artifact_id="ART-COMPAT",
        content="# Spec\n\nChamber pressure nominal.\n",
    )

    bundle_path = tmp_path / "indexes" / "w7_index_bundle.json"
    payload = bundle_path.read_text(encoding="utf-8")

    assert "embedding_configuration_hash" in payload
    assert "cosmos-local-neural-mini-v1" in payload


def test_model_mismatch_raises_schema_error(tmp_path) -> None:
    neural = ProductionLocalRAGPipeline(tmp_path, embedding_mode="neural")
    neural.initialize()
    neural.ingest_document(
        document_id="DOC-MISMATCH",
        source_id="SRC-MISMATCH",
        artifact_id="ART-MISMATCH",
        content="# Spec\n\nThrust vector control.\n",
    )

    deterministic_backend = create_embedding_backend("deterministic")
    manager = IndexLifecycleManager(
        indexes_dir=tmp_path / "indexes",
        embedding_model=deterministic_backend.identity,
        vector_dimension=deterministic_backend.identity.dimension,
        embedding_backend=deterministic_backend,
    )

    with pytest.raises(SchemaMismatchError):
        manager.load(neural.store.graph_store)
