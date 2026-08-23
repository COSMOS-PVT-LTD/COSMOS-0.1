"""Step 7 local knowledge store tests."""

from __future__ import annotations

from knowledge.graph import GraphConstructionBatch, GraphConstructor, ProvenanceReference
from knowledge.extraction import CandidateEntityExtraction, ExtractedEntityKind
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.ontology import OntologyRegistry
from knowledge.storage import LocalKnowledgeStore
from knowledge.storage.index_lifecycle import IndexLifecycleManager
from knowledge.embeddings import DeterministicLocalEmbeddingBackend


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


def test_local_store_persists_graph_across_restart(tmp_path) -> None:
    """Graph snapshot must survive store reload."""

    store = LocalKnowledgeStore(tmp_path)
    store.initialize()
    result = GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(entity_extractions=(_entity(),)),
    )
    store.graph_store.restore(result.store.snapshot())
    digest = store.save_graph()

    reloaded = LocalKnowledgeStore(tmp_path)
    manifest = reloaded.load()

    assert manifest.graph_digest == digest
    assert reloaded.graph_store.get_node("ENT-1") is not None


def test_index_lifecycle_build_load_validate(tmp_path) -> None:
    """Index lifecycle must support BUILD, LOAD, and VALIDATE."""

    store = LocalKnowledgeStore(tmp_path)
    store.initialize()
    GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(entity_extractions=(_entity(),)),
    ).store
    result = GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(entity_extractions=(_entity(),)),
    )
    store.graph_store.restore(result.store.snapshot())
    store.save_graph()

    backend = DeterministicLocalEmbeddingBackend(dimension=8)
    manager = IndexLifecycleManager(
        indexes_dir=tmp_path / "indexes",
        embedding_model=backend.identity,
        vector_dimension=8,
    )

    built = manager.build(store.graph_store)
    loaded = manager.load(store.graph_store)
    manager.validate(store.graph_store)

    assert built.source_digest == loaded.source_digest
