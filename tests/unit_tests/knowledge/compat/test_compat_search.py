"""COMPAT-002 — frozen search facade tests."""

from __future__ import annotations

from knowledge.extraction import CandidateEntityExtraction, ExtractedEntityKind
from knowledge.graph import (
    GraphConstructionBatch,
    GraphConstructor,
    GraphQueryService,
    ProvenanceReference,
)
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.indexing.builder import KnowledgeIndexBuilder
from knowledge.indexing.w7 import W7IndexBuilder, deterministic_reference_vector
from knowledge.ontology import OntologyRegistry
from knowledge.search import SearchQuery
from knowledge.search.contracts import RetrievalMode
from knowledge.search.graph_search import GraphSearch
from knowledge.search.hybrid_search import HybridSearch
from knowledge.search.keyword_search import KeywordSearch
from knowledge.search.search_engine import SearchEngine
from knowledge.search.semantic_search import SemanticSearch


def _provenance() -> SourceProvenanceRecord:
    return SourceProvenanceRecord(
        anchor=ProvenanceReference(document_id="DOC-001", page=1),
    )


def _build_w7_stack(*labels: str):
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
    store = GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(entity_extractions=entities),
    ).store
    bundle = W7IndexBuilder().build(store)
    graph_query = GraphQueryService(store)
    return store, bundle, graph_query


def test_keyword_search_facade_matches_canonical_engine() -> None:
    """KeywordSearch must delegate to KeywordSearchEngine."""

    store, bundle, _ = _build_w7_stack("Chamber Pressure")
    facade = KeywordSearch.from_lexical_index(
        bundle.lexical_index,
        source_digest=bundle.source_digest,
        store=store,
    )
    page = facade.search(
        SearchQuery(text="chamber pressure", mode=RetrievalMode.LEXICAL),
    )

    assert page.total_count == 1
    assert page.results[0].target_id == "ENT-1"
    assert facade.canonical_engine is not None


def test_semantic_search_facade_matches_canonical_engine() -> None:
    """SemanticSearch must delegate to SemanticVectorSearchEngine."""

    store, bundle, _ = _build_w7_stack("Chamber Pressure")
    query_vector = deterministic_reference_vector(
        target_id="ENT-1",
        dimension=bundle.vector_index.dimension(),
    )
    facade = SemanticSearch.from_vector_index(
        bundle.vector_index,
        source_digest=bundle.source_digest,
        store=store,
    )
    page = facade.search(
        SearchQuery(text="chamber pressure", mode=RetrievalMode.SEMANTIC),
        query_vector=query_vector,
    )

    assert page.total_count >= 1
    assert facade.canonical_engine is not None


def test_graph_search_facade_matches_canonical_engine() -> None:
    """GraphSearch must delegate to GraphSearchEngine."""

    store, bundle, graph_query = _build_w7_stack("Chamber Pressure")
    facade = GraphSearch.from_graph_index(
        bundle.graph_index,
        graph_query,
        source_digest=bundle.source_digest,
        store=store,
    )
    page = facade.search(
        SearchQuery(text="chamber", mode=RetrievalMode.STRUCTURED),
    )

    assert page.total_count >= 1
    assert facade.canonical_engine is not None


def test_hybrid_search_facade_matches_canonical_engine() -> None:
    """HybridSearch must delegate to HybridSearchEngine."""

    store, bundle, graph_query = _build_w7_stack("Chamber Pressure", "LOX")
    facade = HybridSearch.from_w7_bundle(bundle, graph_query, store)
    page = facade.search(
        SearchQuery(text="chamber pressure", mode=RetrievalMode.HYBRID),
    )

    assert page.total_count >= 1
    assert facade.canonical_engine is not None


def test_search_engine_facade_delegates_to_knowledge_search_engine() -> None:
    """SearchEngine must subclass KnowledgeSearchEngine."""

    store, bundle, graph_query = _build_w7_stack("Chamber Pressure")
    legacy_bundle = KnowledgeIndexBuilder().build(store)
    engine = SearchEngine(legacy_bundle, graph_query, store)
    page = engine.search(
        SearchQuery(text="chamber", mode=RetrievalMode.LEXICAL),
    )

    assert page.total_count == 1
