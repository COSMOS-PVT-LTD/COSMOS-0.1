"""Gate-6 operational failure and recovery matrix tests."""

from __future__ import annotations

import json

import pytest

from knowledge.production.graph_merge import DocumentGraphMerger
from knowledge.production.incremental_ingestion import IncrementalIngestionCoordinator
from knowledge.storage import CorruptionError, LocalKnowledgeStore, SchemaMismatchError
from knowledge.storage.schema import GRAPH_SNAPSHOT_FILENAME, STORE_MANIFEST_FILENAME


def _ingest(store: LocalKnowledgeStore, doc_id: str, content: str) -> None:
    coordinator = IncrementalIngestionCoordinator(store)
    coordinator.ingest_document(
        document_id=doc_id,
        source_id=f"SRC-{doc_id}",
        artifact_id=f"ART-{doc_id}",
        content=content,
    )


def test_failure_corrupted_persistence_detected(tmp_path) -> None:
  store = LocalKnowledgeStore(tmp_path)
  store.initialize()
  _ingest(store, "DOC-A", "# A\n\nChamber pressure.\n")
  store.save_graph()

  (tmp_path / GRAPH_SNAPSHOT_FILENAME).write_text('{"nodes":"bad"}\n', encoding="utf-8")

  with pytest.raises(CorruptionError):
    LocalKnowledgeStore(tmp_path).load()


def test_failure_interrupted_write_tmp_not_loaded(tmp_path) -> None:
  store = LocalKnowledgeStore(tmp_path)
  store.initialize()
  (tmp_path / f"{GRAPH_SNAPSHOT_FILENAME}.tmp").write_text("{}\n", encoding="utf-8")

  reloaded = LocalKnowledgeStore(tmp_path)
  manifest = reloaded.load()
  assert manifest.graph_digest is None or reloaded.verify_integrity()


def test_failure_duplicate_ingestion_idempotent(tmp_path) -> None:
  store = LocalKnowledgeStore(tmp_path)
  store.initialize()
  content = "# A\n\nChamber pressure.\n"
  _ingest(store, "DOC-A", content)
  _ingest(store, "DOC-A", content)
  assert store.ingestion_state.skipped_unchanged_count >= 1


def test_failure_graph_merge_conflict_recorded(tmp_path) -> None:
  from knowledge.graph import GraphConstructionBatch, GraphConstructor, ProvenanceReference
  from knowledge.extraction import CandidateEntityExtraction, ExtractedEntityKind
  from knowledge.graph.entity import CanonicalEntityType
  from knowledge.graph.provenance import SourceProvenanceRecord
  from knowledge.ontology import OntologyRegistry

  store = LocalKnowledgeStore(tmp_path)
  store.initialize()
  entity = CandidateEntityExtraction(
      extraction_id="ENT-SHARED",
      document_id="DOC-B",
      extracted_label="Shared",
      entity_kind=ExtractedEntityKind.QUANTITY,
      canonical_entity_type=CanonicalEntityType.QUANTITY,
      provenance=SourceProvenanceRecord(
          anchor=ProvenanceReference(document_id="DOC-B", page=1),
      ),
  )
  first = GraphConstructor(OntologyRegistry()).construct(
      GraphConstructionBatch(entity_extractions=(entity,)),
  )
  store.graph_store.restore(first.store.snapshot())

  conflict_entity = CandidateEntityExtraction(
      extraction_id="ENT-SHARED",
      document_id="DOC-C",
      extracted_label="Shared Other",
      entity_kind=ExtractedEntityKind.QUANTITY,
      canonical_entity_type=CanonicalEntityType.QUANTITY,
      provenance=SourceProvenanceRecord(
          anchor=ProvenanceReference(document_id="DOC-C", page=1),
      ),
  )
  second = GraphConstructor(OntologyRegistry()).construct(
      GraphConstructionBatch(entity_extractions=(conflict_entity,)),
  )
  result = DocumentGraphMerger().merge_document(
      store.graph_store,
      second.store.snapshot(),
      document_id="DOC-C",
  )

  assert not result.success
  assert result.cross_document_conflicts


def test_failure_invalid_schema_version(tmp_path) -> None:
  store = LocalKnowledgeStore(tmp_path)
  store.initialize()
  _ingest(store, "DOC-A", "# A\n\nChamber pressure.\n")

  manifest_path = tmp_path / STORE_MANIFEST_FILENAME
  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  manifest["schema_version"] = "99.0.0"
  manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

  with pytest.raises(SchemaMismatchError):
    LocalKnowledgeStore(tmp_path).load()
