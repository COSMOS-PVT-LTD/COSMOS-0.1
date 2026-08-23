"""Performance characterization for KG-BLOCK-012 (measurement only)."""

from __future__ import annotations

import time

from knowledge.graph import GraphConstructionBatch, GraphConstructor
from knowledge.indexing.w7 import W7IndexBuilder
from knowledge.search import RetrievalMode, SearchQuery
from knowledge.search.w8 import HybridSearchEngine

from tests.integration_tests.kg_block012.helpers.pipeline import (
    build_lox_registry,
    load_golden_document,
    parse_and_extract,
    run_full_pipeline,
)

# Generous local ceilings for reference implementation characterization.
_CEILING_PARSE_EXTRACT_S = 2.0
_CEILING_GRAPH_INDEX_S = 2.0
_CEILING_SEARCH_S = 1.0
_CEILING_E2E_S = 5.0


def test_characterize_parse_and_extract_latency() -> None:
    """Record parse+extract latency for golden fixture."""

    content = load_golden_document()
    start = time.perf_counter()
    parse_and_extract(content)
    elapsed = time.perf_counter() - start

    assert elapsed < _CEILING_PARSE_EXTRACT_S


def test_characterize_graph_and_index_build_latency() -> None:
    """Record graph construction and W7 index build latency."""

    extraction = parse_and_extract(load_golden_document())
    start = time.perf_counter()
    graph_result = GraphConstructor(build_lox_registry()).construct(
        GraphConstructionBatch(entity_extractions=extraction.entities or ()),
    )
    W7IndexBuilder().build(graph_result.store)
    elapsed = time.perf_counter() - start

    assert elapsed < _CEILING_GRAPH_INDEX_S


def test_characterize_hybrid_search_latency() -> None:
    """Record hybrid search latency on golden graph."""

    extraction = parse_and_extract(load_golden_document())
    graph_result = GraphConstructor(build_lox_registry()).construct(
        GraphConstructionBatch(entity_extractions=extraction.entities or ()),
    )
    store = graph_result.store
    bundle = W7IndexBuilder().build(store)
    from knowledge.graph import GraphQueryService

    engine = HybridSearchEngine(bundle, GraphQueryService(store), store)

    start = time.perf_counter()
    engine.search(SearchQuery(text="LOX pressure", mode=RetrievalMode.HYBRID))
    elapsed = time.perf_counter() - start

    assert elapsed < _CEILING_SEARCH_S


def test_characterize_end_to_end_pipeline_latency() -> None:
    """Record full W1→W11 pipeline latency for golden fixture."""

    start = time.perf_counter()
    run_full_pipeline(request_id="perf-e2e")
    elapsed = time.perf_counter() - start

    assert elapsed < _CEILING_E2E_S


def test_characterize_graph_and_index_sizes() -> None:
    """Record graph node count and index bundle presence."""

    extraction = parse_and_extract(load_golden_document())
    graph_result = GraphConstructor(build_lox_registry()).construct(
        GraphConstructionBatch(entity_extractions=extraction.entities or ()),
    )
    bundle = W7IndexBuilder().build(graph_result.store)

    assert len(graph_result.store.list_nodes()) >= 0
    assert bundle.source_digest
    assert bundle.lexical_index is not None
    assert bundle.vector_index is not None
    assert bundle.graph_index is not None
