"""Unit tests for knowledge.indexing."""

from __future__ import annotations

from knowledge.extraction import (
    CandidateEntityExtraction,
    ExtractedEntityKind,
)
from knowledge.graph import (
    GraphConstructionBatch,
    GraphConstructor,
    GraphLifecycleState,
    ProvenanceReference,
)
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.indexing import (
    KnowledgeIndexBuilder,
    build_lexical_index_from_store,
    tokenize_text,
)
from knowledge.ontology import OntologyRegistry


def _provenance() -> SourceProvenanceRecord:
    return SourceProvenanceRecord(
        anchor=ProvenanceReference(document_id="DOC-001", page=1),
    )


def _build_store():
    entity = CandidateEntityExtraction(
        extraction_id="ENT-PC",
        document_id="DOC-001",
        extracted_label="Chamber Pressure",
        entity_kind=ExtractedEntityKind.QUANTITY,
        canonical_entity_type=CanonicalEntityType.QUANTITY,
        provenance=_provenance(),
    )

    batch = GraphConstructionBatch(entity_extractions=(entity,))
    result = GraphConstructor(OntologyRegistry()).construct(batch)

    return result.store


def test_tokenize_text_is_deterministic() -> None:
    """Tokenization must be stable and normalized."""

    assert tokenize_text("Chamber Pressure Pc") == (
        "chamber",
        "pc",
        "pressure",
    )


def test_lexical_index_build_and_lookup() -> None:
    """Lexical index must support deterministic lookup."""

    store = _build_store()
    index = build_lexical_index_from_store(store)

    matches = index.lookup(("chamber", "pressure"))

    assert len(matches) == 1
    assert matches[0].target_id == "ENT-PC"


def test_lexical_index_detects_stale_state() -> None:
    """Stale indexes must be detectable relative to graph digests."""

    store = _build_store()
    index = build_lexical_index_from_store(store)
    digest = index.metadata().source_digest

    assert not index.is_stale(digest)
    assert index.is_stale("different-digest")


def test_index_builder_rebuild_is_deterministic() -> None:
    """Index rebuild must produce stable bundles."""

    store = _build_store()
    builder = KnowledgeIndexBuilder()

    first = builder.build(store)
    second = builder.rebuild(store)

    assert (
        first.source_digest
        == second.source_digest
        == first.lexical_index.metadata().source_digest
    )
    assert first.semantic_index.statistics().entry_count == (
        second.semantic_index.statistics().entry_count
    )


def test_stale_bundle_detection() -> None:
    """Bundle staleness must reflect graph mutations."""

    store = _build_store()
    builder = KnowledgeIndexBuilder()
    bundle = builder.build(store)

    assert not bundle.is_stale(store)

    from knowledge.graph import GraphNode, GraphNodeIdentity

    store.add_node(
        GraphNode(
            identity=GraphNodeIdentity(
                node_id="ENT-NEW",
                node_type="Quantity",
            ),
            properties={
                "lifecycle_state": GraphLifecycleState.CANDIDATE.value,
                "document_id": "DOC-001",
                "canonical_name": "New Entity",
            },
        ),
    )

    assert bundle.is_stale(store)
