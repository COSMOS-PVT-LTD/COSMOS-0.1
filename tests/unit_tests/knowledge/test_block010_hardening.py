"""Engineering-review hardening tests for KG-BLOCK-010."""

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
    GraphQueryService,
    GraphRelationship,
    ProvenanceReference,
)
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.indexing.exceptions import IndexStaleError, IndexValidationError
from knowledge.indexing.w7 import (
    InMemoryGraphIndex,
    InMemoryVectorIndex,
    VectorRecord,
    W7IndexBuilder,
    build_graph_index_from_store,
    cosine_similarity,
)
from knowledge.indexing.w7.graph_index import GraphIndexAdjacency
from knowledge.ontology import OntologyRegistry
from knowledge.search import SearchQuery
from knowledge.search.contracts import RetrievalMode
from knowledge.search.exceptions import SearchValidationError
from knowledge.search.w8 import (
    GraphSearchEngine,
    HybridComponentWeights,
    HybridSearchEngine,
    KeywordSearchEngine,
    SemanticVectorSearchEngine,
    ValidationAwareSearchEngine,
)
from knowledge.validation.identity import validation_report_digest
from knowledge.validation.models import (
    ValidationCategory,
    ValidationFinding,
    ValidationReport,
    ValidationSeverity,
    ValidationStatus,
)


def _provenance() -> SourceProvenanceRecord:
    return SourceProvenanceRecord(
        anchor=ProvenanceReference(document_id="DOC-001", page=1),
    )


def _build_store(*labels: str):
    entities = tuple(
        CandidateEntityExtraction(
            extraction_id=f"ENT-{index}",
            document_id="DOC-001",
            extracted_label=label,
            entity_kind=ExtractedEntityKind.QUANTITY,
            canonical_entity_type=CanonicalEntityType.QUANTITY,
            provenance=_provenance(),
        )
        for index, label in enumerate(labels, start=1)
    )

    return GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(entity_extractions=entities),
    ).store


def test_hybrid_weights_reject_negative_components() -> None:
    """Hybrid fusion must reject negative component weights."""

    with pytest.raises(SearchValidationError, match="non-negative"):
        HybridComponentWeights(keyword=-0.5, semantic=0.75, graph=0.75)


def test_vector_similarity_filters_non_positive_scores() -> None:
    """Vector similarity must not return orthogonal or opposite matches."""

    index = InMemoryVectorIndex(
        index_id="vector-test",
        source_digest="digest-a",
        records=(
            VectorRecord(
                record_id="a",
                target_id="t1",
                target_type="Quantity",
                vector=(1.0, 0.0),
            ),
            VectorRecord(
                record_id="b",
                target_id="t2",
                target_type="Quantity",
                vector=(0.0, 1.0),
            ),
        ),
    )

    ranked = index.similarity((1.0, 0.0), limit=5)

    assert len(ranked) == 1
    assert ranked[0][0].target_id == "t1"


def test_cosine_similarity_handles_zero_vectors_safely() -> None:
    """Cosine similarity must return 0.0 for zero-norm vectors."""

    assert cosine_similarity((0.0, 0.0), (1.0, 0.0)) == 0.0


def test_cosine_similarity_opposite_vectors_are_negative() -> None:
    """Opposite vectors must produce negative cosine similarity."""

    assert cosine_similarity((1.0, 0.0), (-1.0, 0.0)) == pytest.approx(-1.0)


def test_keyword_search_rejects_stale_graph_with_store_binding() -> None:
    """Keyword search must reject stale indexes when store is provided."""

    store = _build_store("Chamber Pressure")
    bundle = W7IndexBuilder().build(store)
    engine = KeywordSearchEngine(
        bundle.lexical_index,
        source_digest=bundle.source_digest,
        store=store,
    )

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

    with pytest.raises(IndexStaleError):
        engine.search(SearchQuery(text="chamber pressure", mode=RetrievalMode.LEXICAL))


def test_semantic_search_rejects_dimension_mismatch() -> None:
    """Semantic search must reject query vectors with invalid dimensions."""

    store = _build_store("Chamber Pressure")
    bundle = W7IndexBuilder().build(store)
    engine = SemanticVectorSearchEngine(
        bundle.vector_index,
        source_digest=bundle.source_digest,
        store=store,
    )

    with pytest.raises(IndexValidationError, match="dimension"):
        engine.search(
            SearchQuery(text="semantic", mode=RetrievalMode.SEMANTIC),
            query_vector=(1.0,),
        )


def test_graph_index_cycle_adjacency_is_deterministic() -> None:
    """Graph index must represent cycles with deterministic adjacency."""

    store = _build_store("Alpha", "Beta")
    store.add_relationship(
        GraphRelationship(
            relationship_id="REL-AB",
            relationship_type="links",
            source_node_id="ENT-1",
            target_node_id="ENT-2",
        ),
    )
    store.add_relationship(
        GraphRelationship(
            relationship_id="REL-BA",
            relationship_type="links",
            source_node_id="ENT-2",
            target_node_id="ENT-1",
        ),
    )

    first = build_graph_index_from_store(store)
    second = build_graph_index_from_store(store)

    assert first.adjacency() == second.adjacency()
    assert first.neighbors("ENT-1") == ("ENT-2",)


def test_graph_search_missing_node_does_not_crash_cycle() -> None:
    """Graph search must terminate cleanly on cyclic graphs."""

    store = _build_store("Alpha", "Beta")
    store.add_relationship(
        GraphRelationship(
            relationship_id="REL-AB",
            relationship_type="links",
            source_node_id="ENT-1",
            target_node_id="ENT-2",
        ),
    )
    store.add_relationship(
        GraphRelationship(
            relationship_id="REL-BA",
            relationship_type="links",
            source_node_id="ENT-2",
            target_node_id="ENT-1",
        ),
    )
    bundle = W7IndexBuilder().build(store)
    engine = GraphSearchEngine(
        bundle.graph_index,
        GraphQueryService(store),
        source_digest=bundle.source_digest,
        store=store,
        max_traversal_depth=3,
    )

    page = engine.search(SearchQuery(text="alpha", mode=RetrievalMode.STRUCTURED))

    assert page.total_count >= 1


def test_graph_index_neighbors_missing_node_raises() -> None:
    """Graph index must raise for unknown node lookups."""

    store = _build_store("Alpha")
    index = build_graph_index_from_store(store)

    with pytest.raises(Exception, match="not found"):
        index.neighbors("MISSING")


def test_hybrid_search_rejects_all_components_disabled() -> None:
    """Hybrid search must reject configurations with no active components."""

    store = _build_store("Chamber Pressure")
    bundle = W7IndexBuilder().build(store)
    engine = HybridSearchEngine(
        bundle,
        GraphQueryService(store),
        store,
        use_keyword=False,
        use_semantic=False,
        use_graph=False,
    )

    with pytest.raises(SearchValidationError, match="At least one hybrid"):
        engine.search(SearchQuery(text="chamber", mode=RetrievalMode.HYBRID))


def test_hybrid_search_semantic_only_mode() -> None:
    """Hybrid search must support semantic-only component fusion."""

    store = _build_store("Chamber Pressure")
    bundle = W7IndexBuilder().build(store)
    engine = HybridSearchEngine(
        bundle,
        GraphQueryService(store),
        store,
        use_keyword=False,
        use_graph=False,
    )
    page = engine.search(SearchQuery(text="ENT-1", mode=RetrievalMode.HYBRID))

    assert page.total_count >= 1
    assert page.results[0].ranking_reason.startswith("hybrid_fusion:semantic")


def test_validation_aware_search_does_not_mutate_validation_report() -> None:
    """Validation-aware filtering must not mutate W9 validation reports."""

    store = _build_store("Chamber Pressure")
    bundle = W7IndexBuilder().build(store)
    keyword_engine = KeywordSearchEngine(
        bundle.lexical_index,
        source_digest=bundle.source_digest,
        store=store,
    )
    finding = ValidationFinding(
        finding_id="vf-test",
        rule_id="VAL-TEST",
        severity=ValidationSeverity.HIGH,
        category=ValidationCategory.SCHEMA,
        status=ValidationStatus.INVALID,
        object_id="ENT-OTHER",
        message="invalid target",
    )
    report = ValidationReport(
        findings=(finding,),
        report_digest=validation_report_digest(finding.finding_id),
    )
    before = report.to_mapping()
    engine = ValidationAwareSearchEngine(keyword_engine, validation_report=report)
    engine.search(SearchQuery(text="chamber pressure", mode=RetrievalMode.LEXICAL))

    assert report.to_mapping() == before


def test_validation_aware_search_preserves_provenance_on_valid_results() -> None:
    """Validation-aware filtering must preserve provenance on retained results."""

    store = _build_store("Chamber Pressure")
    bundle = W7IndexBuilder().build(store)
    keyword_engine = KeywordSearchEngine(
        bundle.lexical_index,
        source_digest=bundle.source_digest,
        store=store,
    )
    engine = ValidationAwareSearchEngine(keyword_engine)
    page = engine.search(SearchQuery(text="chamber pressure", mode=RetrievalMode.LEXICAL))

    assert page.results[0].document_id == "DOC-001"


def test_deterministic_tie_ordering_for_equal_vector_scores() -> None:
    """Equal vector similarity scores must tie-break by record_id."""

    index = InMemoryVectorIndex(
        index_id="vector-test",
        source_digest="digest-a",
        records=(
            VectorRecord(
                record_id="b",
                target_id="t2",
                target_type="Quantity",
                vector=(1.0, 0.0),
            ),
            VectorRecord(
                record_id="a",
                target_id="t1",
                target_type="Quantity",
                vector=(1.0, 0.0),
            ),
        ),
    )

    ranked = index.similarity((1.0, 0.0), limit=2)

    assert [record.record_id for record, _score in ranked] == ["a", "b"]


def test_graph_index_rejects_duplicate_node_ids() -> None:
    """Graph index must reject duplicate adjacency node identities."""

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


def test_vector_index_rejects_invalid_numeric_components() -> None:
    """Vector validation must reject NaN components."""

    with pytest.raises(IndexValidationError, match="finite"):
        VectorRecord(
            record_id="vec-1",
            target_id="t1",
            target_type="Quantity",
            vector=(math.nan, 1.0),
        )


def test_w7_bundle_identical_rebuild_produces_same_digest() -> None:
    """Equivalent rebuilds must produce identical source digests."""

    store = _build_store("Chamber Pressure")
    builder = W7IndexBuilder()

    first = builder.build(store)
    second = builder.rebuild(store)

    assert first.source_digest == second.source_digest


def test_import_smoke_for_block010_public_apis() -> None:
    """BLOCK-010 public APIs must import cleanly."""

    from knowledge.indexing.w7 import W7IndexBuilder
    from knowledge.search.w8 import HybridSearchEngine

    assert W7IndexBuilder is not None
    assert HybridSearchEngine is not None
