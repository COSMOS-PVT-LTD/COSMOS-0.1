"""Unit tests for KG-BLOCK-010 W7 indexing (KG-033 → KG-035)."""

from __future__ import annotations

import math

import pytest

from knowledge.extraction import (
    CandidateEntityExtraction,
    ExtractedEntityKind,
)
from knowledge.graph import (
    GraphConstructionBatch,
    GraphConstructor,
    GraphLifecycleState,
    GraphNode,
    GraphNodeIdentity,
    GraphRelationship,
    ProvenanceReference,
)
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.indexing import KnowledgeIndexBuilder, build_lexical_index_from_store
from knowledge.indexing.exceptions import IndexStaleError, IndexValidationError
from knowledge.indexing.w7 import (
    InMemoryGraphIndex,
    InMemoryVectorIndex,
    VectorRecord,
    W7IndexBuilder,
    build_graph_index_from_store,
    build_reference_vector_index_from_store,
    cosine_similarity,
    deterministic_reference_vector,
    validate_vector_components,
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
    return GraphConstructor(OntologyRegistry()).construct(batch).store


def test_kg033_lexical_index_remains_deterministic() -> None:
    """KG-033 lexical index must remain deterministic via frozen reference."""

    store = _build_store()
    first = build_lexical_index_from_store(store)
    second = build_lexical_index_from_store(store)

    assert first.lookup(("chamber", "pressure")) == second.lookup(
        ("chamber", "pressure"),
    )


def test_kg034_vector_index_accepts_valid_vectors() -> None:
    """KG-034 must index caller-supplied vectors with deterministic similarity."""

    record = VectorRecord(
        record_id="vec-1",
        target_id="ENT-PC",
        target_type="Quantity",
        vector=(1.0, 0.0, 0.0),
    )
    index = InMemoryVectorIndex(
        index_id="vector-test",
        source_digest="digest-a",
        records=(record,),
    )

    ranked = index.similarity((1.0, 0.0, 0.0), limit=1)

    assert ranked[0][0].target_id == "ENT-PC"
    assert ranked[0][1] == pytest.approx(1.0)


def test_kg034_vector_index_rejects_dimension_mismatch() -> None:
    """KG-034 must reject query vectors with incompatible dimensions."""

    index = InMemoryVectorIndex(
        index_id="vector-test",
        source_digest="digest-a",
        records=(
            VectorRecord(
                record_id="vec-1",
                target_id="ENT-PC",
                target_type="Quantity",
                vector=(1.0, 0.0),
            ),
        ),
    )

    with pytest.raises(IndexValidationError, match="dimension"):
        index.similarity((1.0, 0.0, 0.0), limit=1)


def test_kg034_vector_index_rejects_nan_components() -> None:
    """KG-034 must reject non-finite vector components."""

    with pytest.raises(IndexValidationError, match="finite"):
        validate_vector_components((1.0, math.nan))


def test_kg034_vector_index_rejects_duplicate_record_ids() -> None:
    """KG-034 must reject duplicate vector identities."""

    record = VectorRecord(
        record_id="vec-1",
        target_id="ENT-PC",
        target_type="Quantity",
        vector=(1.0, 0.0),
    )

    with pytest.raises(IndexValidationError, match="Duplicate vector record_id"):
        InMemoryVectorIndex(
            index_id="vector-test",
            source_digest="digest-a",
            records=(record, record),
        )


def test_kg034_cosine_similarity_is_correct() -> None:
    """KG-034 cosine similarity must be mathematically well-defined."""

    assert cosine_similarity((1.0, 0.0), (1.0, 0.0)) == pytest.approx(1.0)
    assert cosine_similarity((1.0, 0.0), (0.0, 1.0)) == pytest.approx(0.0)


def test_kg034_reference_vector_index_builds_from_store() -> None:
    """KG-034 reference index must build deterministic vectors from graph nodes."""

    store = _build_store()
    index = build_reference_vector_index_from_store(store)

    assert index.dimension() == 8
    assert len(index.records()) == 1


def test_kg035_graph_index_supports_adjacency_lookup() -> None:
    """KG-035 must provide deterministic adjacency lookup."""

    store = _build_store()
    store.add_node(
        GraphNode(
            identity=GraphNodeIdentity(node_id="ENT-REL", node_type="Quantity"),
            properties={
                "lifecycle_state": GraphLifecycleState.CANDIDATE.value,
                "document_id": "DOC-001",
                "canonical_name": "Related",
            },
        ),
    )
    store.add_relationship(
        GraphRelationship(
            relationship_id="REL-1",
            relationship_type="DESCRIBES",
            source_node_id="ENT-PC",
            target_node_id="ENT-REL",
        ),
    )

    index = build_graph_index_from_store(store)

    assert index.neighbors("ENT-PC") == ("ENT-REL",)
    assert index.neighbors("ENT-REL") == ("ENT-PC",)


def test_kg035_graph_index_detects_stale_state() -> None:
    """KG-035 must detect stale graph indexes."""

    store = _build_store()
    index = build_graph_index_from_store(store)
    digest = index.metadata().source_digest

    assert not index.is_stale(digest)
    assert index.is_stale("different-digest")


def test_w7_bundle_rebuild_is_deterministic() -> None:
    """W7 bundle rebuild must produce stable digests."""

    store = _build_store()
    builder = W7IndexBuilder()

    first = builder.build(store)
    second = builder.rebuild(store)

    assert first.source_digest == second.source_digest
    assert (
        first.vector_index.metadata().source_digest
        == second.vector_index.metadata().source_digest
    )


def test_w7_bundle_detects_stale_after_graph_mutation() -> None:
    """W7 bundle must detect staleness after graph mutation."""

    store = _build_store()
    bundle = W7IndexBuilder().build(store)

    assert not bundle.is_stale(store)

    store.add_node(
        GraphNode(
            identity=GraphNodeIdentity(node_id="ENT-NEW", node_type="Quantity"),
            properties={
                "lifecycle_state": GraphLifecycleState.CANDIDATE.value,
                "document_id": "DOC-001",
                "canonical_name": "New",
            },
        ),
    )

    assert bundle.is_stale(store)


def test_frozen_lexical_builder_still_works_with_w7_bundle() -> None:
    """Frozen KG-033 builder must compose with W7 bundle."""

    store = _build_store()
    frozen_bundle = KnowledgeIndexBuilder().build(store)
    w7_bundle = W7IndexBuilder().build(store)

    assert (
        frozen_bundle.lexical_index.metadata().source_digest
        == w7_bundle.lexical_index.metadata().source_digest
    )


def test_kg034_empty_vector_index_returns_no_matches() -> None:
    """KG-034 empty vector index must return no similarity matches."""

    index = InMemoryVectorIndex(
        index_id="vector-empty",
        source_digest="digest-a",
        records=(),
    )

    assert index.similarity((1.0,), limit=5) == ()


def test_kg035_graph_index_rejects_duplicate_node_ids() -> None:
    """KG-035 must reject duplicate adjacency node identities."""

    from knowledge.indexing.w7.graph_index import GraphIndexAdjacency

    record = GraphIndexAdjacency(
        node_id="ENT-1",
        node_type="Quantity",
        neighbor_ids=(),
        relationship_ids=(),
    )

    with pytest.raises(IndexValidationError, match="Duplicate graph index node_id"):
        InMemoryGraphIndex(
            index_id="graph-test",
            source_digest="digest-a",
            adjacency_records=(record, record),
        )


def test_kg034_stale_vector_index_raises_on_require_fresh() -> None:
    """KG-034 stale vector index must raise on freshness check."""

    from knowledge.indexing.w7.vector import require_fresh_vector_index

    index = build_reference_vector_index_from_store(_build_store())

    with pytest.raises(IndexStaleError):
        require_fresh_vector_index(index, "stale-digest")


def test_kg034_deterministic_reference_vector_is_stable() -> None:
    """KG-034 reference vectors must be stable for identical targets."""

    first = deterministic_reference_vector(target_id="ENT-PC", dimension=4)
    second = deterministic_reference_vector(target_id="ENT-PC", dimension=4)

    assert first == second
