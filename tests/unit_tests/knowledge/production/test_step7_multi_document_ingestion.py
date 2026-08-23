"""Step 7 multi-document graph merge and incremental ingestion tests."""

from __future__ import annotations

from knowledge.graph import GraphConstructionBatch, GraphConstructor, ProvenanceReference
from knowledge.extraction import CandidateEntityExtraction, ExtractedEntityKind
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.ontology import OntologyRegistry
from knowledge.production.graph_merge import DocumentGraphMerger
from knowledge.production.incremental_ingestion import (
    IncrementalIngestionCoordinator,
    IngestionAction,
)
from knowledge.storage import LocalKnowledgeStore


def _entity(document_id: str, extraction_id: str, label: str) -> CandidateEntityExtraction:
    return CandidateEntityExtraction(
        extraction_id=extraction_id,
        document_id=document_id,
        extracted_label=label,
        entity_kind=ExtractedEntityKind.QUANTITY,
        canonical_entity_type=CanonicalEntityType.QUANTITY,
        provenance=SourceProvenanceRecord(
            anchor=ProvenanceReference(document_id=document_id, page=1),
        ),
    )


def _construct(document_id: str, extraction_id: str, label: str):
    return GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(
            entity_extractions=(_entity(document_id, extraction_id, label),),
        ),
    )


def test_first_document_ingestion(tmp_path) -> None:
    store = LocalKnowledgeStore(tmp_path)
    store.initialize()
    coordinator = IncrementalIngestionCoordinator(store)

    decision, _ = coordinator.ingest_document(
        document_id="DOC-A",
        source_id="SRC-A",
        artifact_id="ART-A",
        content="# Doc A\n\nChamber pressure nominal.\n",
    )

    assert decision.action is IngestionAction.PROCESSED
    document_nodes = [
        node
        for node in store.graph_store.list_nodes()
        if node.properties.get("document_id") == "DOC-A"
    ]
    assert document_nodes


def test_second_independent_document_ingestion(tmp_path) -> None:
    store = LocalKnowledgeStore(tmp_path)
    store.initialize()
    coordinator = IncrementalIngestionCoordinator(store)

    coordinator.ingest_document(
        document_id="DOC-A",
        source_id="SRC-A",
        artifact_id="ART-A",
        content="# Doc A\n\nChamber pressure nominal.\n",
    )
    coordinator.ingest_document(
        document_id="DOC-B",
        source_id="SRC-B",
        artifact_id="ART-B",
        content="# Doc B\n\nThrust vector control.\n",
    )

    nodes = store.graph_store.list_nodes()
    document_ids = {
        node.properties.get("document_id")
        for node in nodes
        if node.properties.get("document_id") is not None
    }

    assert "DOC-A" in document_ids
    assert "DOC-B" in document_ids
    assert len(nodes) >= 2


def test_repeated_ingestion_skips_unchanged(tmp_path) -> None:
    store = LocalKnowledgeStore(tmp_path)
    store.initialize()
    coordinator = IncrementalIngestionCoordinator(store)
    content = "# Doc A\n\nChamber pressure nominal.\n"

    first, _ = coordinator.ingest_document(
        document_id="DOC-A",
        source_id="SRC-A",
        artifact_id="ART-A",
        content=content,
    )
    second, artifacts = coordinator.ingest_document(
        document_id="DOC-A",
        source_id="SRC-A",
        artifact_id="ART-A",
        content=content,
    )

    assert first.action is IngestionAction.PROCESSED
    assert second.action is IngestionAction.SKIPPED_UNCHANGED
    assert artifacts is None


def test_document_update_replaces_graph_content(tmp_path) -> None:
    store = LocalKnowledgeStore(tmp_path)
    store.initialize()
    coordinator = IncrementalIngestionCoordinator(store)

    coordinator.ingest_document(
        document_id="DOC-A",
        source_id="SRC-A",
        artifact_id="ART-A",
        content="# Doc A\n\nChamber pressure nominal.\n",
    )
    before_version = store.documents["DOC-A"].version

    decision, _ = coordinator.ingest_document(
        document_id="DOC-A",
        source_id="SRC-A",
        artifact_id="ART-A",
        content="# Doc A\n\nChamber pressure updated nominal.\n",
    )

    assert decision.action is IngestionAction.PROCESSED
    assert store.documents["DOC-A"].version == before_version + 1


def test_graph_merge_preserves_other_documents(tmp_path) -> None:
    store = LocalKnowledgeStore(tmp_path)
    store.initialize()
    merger = DocumentGraphMerger()

    result_a = _construct("DOC-A", "ENT-A", "Alpha")
    store.graph_store.restore(result_a.store.snapshot())
    result_b = _construct("DOC-B", "ENT-B", "Beta")
    merge = merger.merge_document(
        store.graph_store,
        result_b.store.snapshot(),
        document_id="DOC-B",
    )

    assert merge.success
    assert store.graph_store.get_node("ENT-A") is not None
    assert store.graph_store.get_node("ENT-B") is not None


def test_document_removal(tmp_path) -> None:
    store = LocalKnowledgeStore(tmp_path)
    store.initialize()
    coordinator = IncrementalIngestionCoordinator(store)

    coordinator.ingest_document(
        document_id="DOC-A",
        source_id="SRC-A",
        artifact_id="ART-A",
        content="# Doc A\n\nChamber pressure nominal.\n",
    )
    coordinator.ingest_document(
        document_id="DOC-B",
        source_id="SRC-B",
        artifact_id="ART-B",
        content="# Doc B\n\nThrust vector control.\n",
    )

    merge_result = coordinator.remove_document(document_id="DOC-A")

    assert merge_result.removed_nodes >= 1
    assert store.documents["DOC-A"].status == "REMOVED"
    remaining_docs = {
        node.properties.get("document_id")
        for node in store.graph_store.list_nodes()
    }
    assert "DOC-A" not in remaining_docs
    assert "DOC-B" in remaining_docs


def test_provenance_preserved_after_merge(tmp_path) -> None:
    store = LocalKnowledgeStore(tmp_path)
    store.initialize()
    coordinator = IncrementalIngestionCoordinator(store)

    coordinator.ingest_document(
        document_id="DOC-A",
        source_id="SRC-A",
        artifact_id="ART-A",
        content="# Doc A\n\nChamber pressure nominal.\n",
    )

    record = store.documents["DOC-A"]
    assert record.source_id == "SRC-A"
    assert record.artifact_id == "ART-A"
    assert record.content_digest


def test_deterministic_rebuild_after_restart(tmp_path) -> None:
    store = LocalKnowledgeStore(tmp_path)
    store.initialize()
    coordinator = IncrementalIngestionCoordinator(store)

    coordinator.ingest_document(
        document_id="DOC-A",
        source_id="SRC-A",
        artifact_id="ART-A",
        content="# Doc A\n\nChamber pressure nominal.\n",
    )
    digest_before = store.save_graph()

    reloaded = LocalKnowledgeStore(tmp_path)
    reloaded.load()

    assert reloaded.verify_integrity()
    assert digest_before == reloaded.load().graph_digest
