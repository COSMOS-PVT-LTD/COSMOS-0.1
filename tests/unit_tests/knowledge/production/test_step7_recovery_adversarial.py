"""Step 7 adversarial recovery and failure qualification tests."""

from __future__ import annotations

import json

import pytest

from knowledge.embeddings import DeterministicLocalEmbeddingBackend
from knowledge.graph import GraphConstructionBatch, GraphConstructor, ProvenanceReference
from knowledge.extraction import CandidateEntityExtraction, ExtractedEntityKind
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.ontology import OntologyRegistry
from knowledge.production.recovery import RecoveryAction, RecoveryProcedure
from knowledge.storage import CorruptionError, LocalKnowledgeStore, SchemaMismatchError
from knowledge.storage.index_lifecycle import IndexLifecycleManager
from knowledge.storage.schema import (
    GRAPH_SNAPSHOT_FILENAME,
    PRODUCTION_SCHEMA_VERSION,
    STORE_MANIFEST_FILENAME,
)


def _entity() -> CandidateEntityExtraction:
    return CandidateEntityExtraction(
        extraction_id="ENT-1",
        document_id="DOC-001",
        extracted_label="Chamber Pressure",
        entity_kind=ExtractedEntityKind.QUANTITY,
        canonical_entity_type=CanonicalEntityType.QUANTITY,
        provenance=SourceProvenanceRecord(
            anchor=ProvenanceReference(document_id="DOC-001", page=1),
        ),
    )


def _seed_store(tmp_path) -> LocalKnowledgeStore:
    store = LocalKnowledgeStore(tmp_path)
    store.initialize()
    result = GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(entity_extractions=(_entity(),)),
    )
    store.graph_store.restore(result.store.snapshot())
    store.save_graph()
    store.load()
    return store


def test_corrupted_graph_snapshot_detected(tmp_path) -> None:
    store = _seed_store(tmp_path)
    assert store.verify_integrity()

    graph_path = tmp_path / GRAPH_SNAPSHOT_FILENAME
    graph_path.write_text('{"nodes": "invalid"}\n', encoding="utf-8")

    with pytest.raises(CorruptionError):
        corrupted = LocalKnowledgeStore(tmp_path)
        corrupted.load()


def test_incompatible_schema_version(tmp_path) -> None:
    store = _seed_store(tmp_path)
    manifest_path = tmp_path / STORE_MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = "99.0.0"
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

    with pytest.raises(SchemaMismatchError):
        LocalKnowledgeStore(tmp_path).load()


def test_stale_index_triggers_rebuild(tmp_path) -> None:
    store = _seed_store(tmp_path)
    backend = DeterministicLocalEmbeddingBackend(dimension=8)
    manager = IndexLifecycleManager(
        indexes_dir=tmp_path / "indexes",
        embedding_model=backend.identity,
        vector_dimension=8,
    )
    manager.build(store.graph_store)

    result = GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(
            entity_extractions=(
                CandidateEntityExtraction(
                    extraction_id="ENT-2",
                    document_id="DOC-002",
                    extracted_label="Thrust",
                    entity_kind=ExtractedEntityKind.QUANTITY,
                    canonical_entity_type=CanonicalEntityType.QUANTITY,
                    provenance=SourceProvenanceRecord(
                        anchor=ProvenanceReference(document_id="DOC-002", page=1),
                    ),
                ),
            ),
        ),
    )
    store.graph_store.restore(result.store.snapshot())
    store.save_graph()

    recovery = RecoveryProcedure(store=store, index_manager=manager)
    plan = recovery.diagnose()

    assert RecoveryAction.REBUILD_INDEXES in plan.actions


def test_missing_index_rebuilds(tmp_path) -> None:
    store = _seed_store(tmp_path)
    backend = DeterministicLocalEmbeddingBackend(dimension=8)
    manager = IndexLifecycleManager(
        indexes_dir=tmp_path / "indexes",
        embedding_model=backend.identity,
        vector_dimension=8,
    )

    recovery = RecoveryProcedure(store=store, index_manager=manager)
    bundle = recovery.recover()

    assert bundle.source_digest


def test_recovery_from_corruption_raises(tmp_path) -> None:
    store = _seed_store(tmp_path)
    backend = DeterministicLocalEmbeddingBackend(dimension=8)
    manager = IndexLifecycleManager(
        indexes_dir=tmp_path / "indexes",
        embedding_model=backend.identity,
        vector_dimension=8,
    )
    graph_path = tmp_path / GRAPH_SNAPSHOT_FILENAME
    graph_path.write_text("{}\n", encoding="utf-8")

    recovery = RecoveryProcedure(store=store, index_manager=manager)

    with pytest.raises(CorruptionError):
        recovery.recover_from_corruption()


def test_interrupted_persistence_tmp_file_not_committed(tmp_path) -> None:
    store = LocalKnowledgeStore(tmp_path)
    store.initialize()
    tmp_file = tmp_path / "graph_snapshot.json.tmp"
    tmp_file.write_text('{"nodes": [], "relationships": []}\n', encoding="utf-8")

    reloaded = LocalKnowledgeStore(tmp_path)
    manifest = reloaded.load()

    assert manifest.schema_version == PRODUCTION_SCHEMA_VERSION
    assert not (tmp_path / GRAPH_SNAPSHOT_FILENAME).exists() or reloaded.verify_integrity()
