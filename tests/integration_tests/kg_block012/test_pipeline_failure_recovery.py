"""Failure and recovery verification for KG-BLOCK-012."""

from __future__ import annotations

import pytest

from knowledge.graph import (
    GraphConstructionBatch,
    GraphConstructor,
    GraphNode,
    GraphNodeIdentity,
    GraphLifecycleState,
)
from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.indexing.exceptions import IndexStaleError
from knowledge.indexing.w7 import W7IndexBuilder
from knowledge.interface import ControlledRAGOrchestrator, ControlledRAGRequest
from knowledge.interface.exceptions import InterfaceValidationError
from knowledge.reasoning.evidence import EvidenceBundle, EvidenceItem, RankingMetadata
from knowledge.reasoning.exceptions import ReasoningValidationError
from knowledge.reasoning.w10 import EvidenceChainBuilder, W10EngineeringContextBuilder
from knowledge.search import RetrievalMode, SearchQuery
from knowledge.search.exceptions import SearchValidationError
from knowledge.search.w8 import HybridSearchEngine, KeywordSearchEngine

from tests.integration_tests.kg_block012.helpers.pipeline import (
    build_lox_registry,
    load_golden_document,
    parse_and_extract,
    run_full_pipeline,
)


def test_malformed_blank_query_rejected() -> None:
    """Invalid search queries must fail with domain validation errors."""

    artifacts = run_full_pipeline()

    with pytest.raises(SearchValidationError):
        HybridSearchEngine(
            artifacts.index_bundle,
            artifacts.graph_query,
            artifacts.store,
        ).search(SearchQuery(text="   ", mode=RetrievalMode.HYBRID))


def test_missing_provenance_document_id_visible_on_chain() -> None:
    """Missing document identity must be visible without silent success."""

    chain = EvidenceChainBuilder().build_chain(
        proposition="test",
        evidence=EvidenceBundle(
            items=(
                EvidenceItem(
                    target_id="ENT-NO-DOC",
                    target_type="Quantity",
                    document_id=None,
                    lifecycle_state="CANDIDATE",
                    provenance={},
                    ranking=RankingMetadata(
                        rank=1,
                        score=1.0,
                        ranking_reason="test",
                        tie_breaker="ENT-NO-DOC",
                    ),
                ),
            ),
            has_verified_results=False,
        ),
    )

    assert chain.missing_source is True


def test_stale_index_rejected_on_search() -> None:
    """Stale indexes must raise IndexStaleError when store is bound."""

    extraction = parse_and_extract(load_golden_document())
    graph_result = GraphConstructor(build_lox_registry()).construct(
        GraphConstructionBatch(entity_extractions=extraction.entities or ()),
    )
    store = graph_result.store
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
                "document_id": extraction.document_id,
                "canonical_name": "Mutation Marker",
            },
        ),
    )

    with pytest.raises(IndexStaleError):
        engine.search(SearchQuery(text="mutation", mode=RetrievalMode.LEXICAL))


def test_invalid_reasoning_context_rejected() -> None:
    """Blank task must fail context assembly deterministically."""

    with pytest.raises(ReasoningValidationError):
        W10EngineeringContextBuilder().build(
            task="   ",
            query=SearchQuery(text="test", mode=RetrievalMode.HYBRID),
            evidence=EvidenceBundle(items=(), has_verified_results=False),
        )


def test_invalid_interface_request_rejected() -> None:
    """Blank controlled RAG task must fail interface validation."""

    artifacts = run_full_pipeline()

    with pytest.raises(InterfaceValidationError):
        ControlledRAGOrchestrator(
            index_bundle=artifacts.index_bundle,
            graph_query=artifacts.graph_query,
            store=artifacts.store,
        ).retrieve(
            ControlledRAGRequest(
                request_id="fail-001",
                task="   ",
                query=SearchQuery(text="LOX", mode=RetrievalMode.HYBRID),
            ),
        )


def test_empty_extraction_on_minimal_document() -> None:
    """Documents without extractable engineering content must not crash pipeline."""

    content = "No engineering entities or headings in this document.\n"
    extraction = parse_and_extract(content)

    assert extraction.document_id
    assert not extraction.entities


def test_graph_mutation_does_not_corrupt_prior_digest_binding() -> None:
    """Graph mutation after indexing must change digest and reject stale search."""

    extraction = parse_and_extract(load_golden_document())
    graph_result = GraphConstructor(build_lox_registry()).construct(
        GraphConstructionBatch(entity_extractions=extraction.entities or ()),
    )
    store = graph_result.store
    bundle = W7IndexBuilder().build(store)
    before_digest = canonical_graph_record_digest(store.snapshot())

    store.add_node(
        GraphNode(
            identity=GraphNodeIdentity(node_id="ENT-FAIL", node_type="Quantity"),
            properties={
                "lifecycle_state": GraphLifecycleState.CANDIDATE.value,
                "document_id": extraction.document_id,
                "canonical_name": "Failure Marker",
            },
        ),
    )
    after_digest = canonical_graph_record_digest(store.snapshot())

    assert before_digest != after_digest
    assert bundle.is_stale(store)
