"""Unit tests for KG-BLOCK-010 W8 search (KG-036 → KG-039)."""

from __future__ import annotations

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
    ProvenanceReference,
)
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.indexing.exceptions import IndexStaleError, IndexValidationError
from knowledge.indexing.w7 import W7IndexBuilder, deterministic_reference_vector
from knowledge.ontology import OntologyRegistry
from knowledge.search import SearchFilter, SearchQuery
from knowledge.search.contracts import RetrievalMode
from knowledge.search.exceptions import SearchValidationError
from knowledge.search.w8 import (
    GraphSearchEngine,
    HybridSearchEngine,
    KeywordSearchEngine,
    SemanticVectorSearchEngine,
    ValidationAwareSearchEngine,
)
from knowledge.validation import ValidationContext, validate_context
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


def _build_w7_stack(*labels: str):
    store = _build_store(*labels)
    bundle = W7IndexBuilder().build(store)
    graph_query = GraphQueryService(store)

    return store, bundle, graph_query


def test_kg036_keyword_search_exact_match() -> None:
    """KG-036 must return deterministic keyword matches."""

    store, bundle, _ = _build_w7_stack("Chamber Pressure")
    engine = KeywordSearchEngine(
        bundle.lexical_index,
        source_digest=bundle.source_digest,
    )
    page = engine.search(SearchQuery(text="chamber pressure", mode=RetrievalMode.LEXICAL))

    assert page.total_count == 1
    assert page.results[0].target_id == "ENT-1"
    assert page.results[0].ranking_reason == "keyword_exact_token_match"


def test_kg036_keyword_search_empty_query_terms_returns_empty() -> None:
    """KG-036 must handle queries with no matching tokens."""

    _, bundle, _ = _build_w7_stack("Chamber Pressure")
    engine = KeywordSearchEngine(
        bundle.lexical_index,
        source_digest=bundle.source_digest,
    )
    page = engine.search(SearchQuery(text="zzz", mode=RetrievalMode.LEXICAL))

    assert page.total_count == 0


def test_kg037_semantic_search_uses_supplied_vectors() -> None:
    """KG-037 must rank results using caller-supplied query vectors only."""

    _, bundle, _ = _build_w7_stack("Chamber Pressure")
    engine = SemanticVectorSearchEngine(
        bundle.vector_index,
        source_digest=bundle.source_digest,
    )
    query_vector = deterministic_reference_vector(
        target_id="ENT-1",
        dimension=bundle.vector_index.dimension(),
    )
    page = engine.search(
        SearchQuery(text="semantic-query", mode=RetrievalMode.SEMANTIC),
        query_vector=query_vector,
    )

    assert page.total_count >= 1
    assert page.results[0].ranking_reason == "semantic_vector_cosine_similarity"


def test_kg037_semantic_search_rejects_invalid_query_vector() -> None:
    """KG-037 must reject invalid query vector dimensions."""

    _, bundle, _ = _build_w7_stack("Chamber Pressure")
    engine = SemanticVectorSearchEngine(
        bundle.vector_index,
        source_digest=bundle.source_digest,
    )

    with pytest.raises(IndexValidationError, match="dimension"):
        engine.search(
            SearchQuery(text="semantic-query", mode=RetrievalMode.SEMANTIC),
            query_vector=(1.0,),
        )


def test_kg038_graph_search_returns_provenance_aware_results() -> None:
    """KG-038 must return graph-aware results with provenance metadata."""

    store, bundle, graph_query = _build_w7_stack("Chamber Pressure")
    engine = GraphSearchEngine(
        bundle.graph_index,
        graph_query,
        source_digest=bundle.source_digest,
    )
    page = engine.search(SearchQuery(text="chamber", mode=RetrievalMode.STRUCTURED))

    assert page.total_count >= 1
    assert page.results[0].document_id == "DOC-001"


def test_kg039_hybrid_search_is_deterministic() -> None:
    """KG-039 hybrid fusion must be deterministic."""

    store, bundle, graph_query = _build_w7_stack("Chamber Pressure")
    engine = HybridSearchEngine(bundle, graph_query, store)
    query = SearchQuery(text="chamber pressure", mode=RetrievalMode.HYBRID)

    first = engine.search(query)
    second = engine.search(query)

    assert first.to_mapping() == second.to_mapping()


def test_kg039_hybrid_search_lexical_only_component() -> None:
    """KG-039 must support lexical-only hybrid mode."""

    store, bundle, graph_query = _build_w7_stack("Chamber Pressure")
    engine = HybridSearchEngine(
        bundle,
        graph_query,
        store,
        use_semantic=False,
        use_graph=False,
    )
    page = engine.search(SearchQuery(text="chamber pressure", mode=RetrievalMode.HYBRID))

    assert page.total_count >= 1
    assert page.results[0].ranking_reason.startswith("hybrid_fusion:keyword")


def test_kg039_hybrid_search_rejects_stale_indexes() -> None:
    """KG-039 must reject stale hybrid indexes."""

    store, bundle, graph_query = _build_w7_stack("Chamber Pressure")
    engine = HybridSearchEngine(bundle, graph_query, store)

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
        engine.search(SearchQuery(text="chamber", mode=RetrievalMode.HYBRID))


def test_kg039_hybrid_search_deduplicates_results() -> None:
    """KG-039 must fuse duplicate target IDs from multiple components."""

    store, bundle, graph_query = _build_w7_stack("Chamber Pressure")
    engine = HybridSearchEngine(bundle, graph_query, store)
    page = engine.search(SearchQuery(text="chamber pressure", mode=RetrievalMode.HYBRID))

    target_ids = [result.target_id for result in page.results]

    assert len(target_ids) == len(set(target_ids))


def test_lifecycle_filtering_excludes_non_matching_results() -> None:
    """Search filters must respect lifecycle constraints."""

    _, bundle, _ = _build_w7_stack("Chamber Pressure")
    engine = KeywordSearchEngine(
        bundle.lexical_index,
        source_digest=bundle.source_digest,
    )
    page = engine.search(
        SearchQuery(
            text="chamber pressure",
            mode=RetrievalMode.LEXICAL,
            filters=SearchFilter(lifecycle_state="APPROVED"),
        ),
    )

    assert page.total_count == 0


def test_validation_aware_search_filters_invalid_targets() -> None:
    """Validation-aware search must exclude INVALID validation targets."""

    _, bundle, _ = _build_w7_stack("Chamber Pressure")
    keyword_engine = KeywordSearchEngine(
        bundle.lexical_index,
        source_digest=bundle.source_digest,
    )
    finding = ValidationFinding(
        finding_id="vf-test",
        rule_id="VAL-TEST",
        severity=ValidationSeverity.HIGH,
        category=ValidationCategory.SCHEMA,
        status=ValidationStatus.INVALID,
        object_id="ENT-1",
        message="invalid target",
    )
    report = ValidationReport(
        findings=(finding,),
        report_digest=validation_report_digest(finding.finding_id),
    )
    engine = ValidationAwareSearchEngine(
        keyword_engine,
        validation_report=report,
    )
    page = engine.search(SearchQuery(text="chamber pressure", mode=RetrievalMode.LEXICAL))

    assert page.total_count == 0


def test_integration_graph_index_search_validation_path() -> None:
    """GRAPH → INDEX → SEARCH → VALIDATION-AWARE path must preserve provenance."""

    from tests.unit_tests.knowledge.extraction.test_w4_extraction import (
        _parse_and_extract,
    )

    extraction = _parse_and_extract("Material: LOX\nOperating pressure 5 MPa.\n")
    validation_report = validate_context(
        ValidationContext(
            document_id=extraction.document_id,
            source_id=extraction.source_id,
            extraction_result=extraction,
        ),
    )

    store = _build_store("Chamber Pressure")
    bundle = W7IndexBuilder().build(store)
    graph_query = GraphQueryService(store)
    hybrid = ValidationAwareSearchEngine(
        HybridSearchEngine(bundle, graph_query, store),
        validation_report=validation_report,
    )
    page = hybrid.search(SearchQuery(text="chamber pressure", mode=RetrievalMode.HYBRID))

    assert validation_report.report_digest
    assert page.results
    assert page.results[0].document_id == "DOC-001"
    assert not hybrid.has_verified_results(page)


def test_search_rejects_invalid_limit() -> None:
    """Search contracts must reject invalid pagination limits."""

    _, bundle, _ = _build_w7_stack("Chamber Pressure")
    engine = KeywordSearchEngine(
        bundle.lexical_index,
        source_digest=bundle.source_digest,
    )

    with pytest.raises(SearchValidationError, match="limit"):
        engine.search(SearchQuery(text="chamber", mode=RetrievalMode.LEXICAL, limit=0))
