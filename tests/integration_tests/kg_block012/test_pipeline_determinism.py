"""Determinism and reproducibility verification for KG-BLOCK-012."""

from __future__ import annotations

from knowledge.extraction import (
    CandidateEntityExtraction,
    ExtractedEntityKind,
)
from knowledge.graph import GraphConstructionBatch, GraphConstructor, ProvenanceReference
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.indexing.w7 import W7IndexBuilder
from knowledge.reasoning.w10 import EvidenceChainBuilder
from knowledge.reasoning.evidence import EvidenceBundle, EvidenceItem, RankingMetadata
from knowledge.search import RetrievalMode, SearchQuery
from knowledge.search.w8 import HybridSearchEngine

from tests.integration_tests.kg_block012.helpers.pipeline import (
    build_lox_registry,
    load_golden_document,
    parse_and_extract,
    run_full_pipeline,
)


def test_repeated_pipeline_execution_is_identical() -> None:
    """Repeated golden pipeline runs must produce identical interface digests."""

    first = run_full_pipeline(request_id="determinism-1")
    second = run_full_pipeline(request_id="determinism-1")

    assert first.payload.to_mapping() == second.payload.to_mapping()


def test_repeated_index_build_produces_identical_digest() -> None:
    """Repeated W7 index builds must bind the same graph digest."""

    extraction = parse_and_extract(load_golden_document())
    graph_result = GraphConstructor(build_lox_registry()).construct(
        GraphConstructionBatch(entity_extractions=extraction.entities or ()),
    )
    store = graph_result.store
    first = W7IndexBuilder().build(store)
    second = W7IndexBuilder().build(store)

    assert first.source_digest == second.source_digest
    assert first.source_digest == canonical_graph_record_digest(store.snapshot())


def test_repeated_search_results_are_identical() -> None:
    """Repeated W8 search must return identical result pages."""

    extraction = parse_and_extract(load_golden_document())
    graph_result = GraphConstructor(build_lox_registry()).construct(
        GraphConstructionBatch(entity_extractions=extraction.entities or ()),
    )
    store = graph_result.store
    bundle = W7IndexBuilder().build(store)
    from knowledge.graph import GraphQueryService

    query_service = GraphQueryService(store)
    engine = HybridSearchEngine(bundle, query_service, store)
    request = SearchQuery(text="LOX pressure", mode=RetrievalMode.HYBRID)

    first = engine.search(request)
    second = engine.search(request)

    assert first.to_mapping() == second.to_mapping()


def test_evidence_chain_ordering_independent_of_input_order() -> None:
    """Evidence chain construction must be stable under input reversal."""

    items = (
        EvidenceItem(
            target_id="ENT-B",
            target_type="Quantity",
            document_id="DOC-001",
            lifecycle_state="CANDIDATE",
            provenance={"document_id": "DOC-001"},
            ranking=RankingMetadata(
                rank=1,
                score=1.0,
                ranking_reason="test",
                tie_breaker="ENT-B",
            ),
        ),
        EvidenceItem(
            target_id="ENT-A",
            target_type="Quantity",
            document_id="DOC-001",
            lifecycle_state="CANDIDATE",
            provenance={"document_id": "DOC-001"},
            ranking=RankingMetadata(
                rank=2,
                score=0.9,
                ranking_reason="test",
                tie_breaker="ENT-A",
            ),
        ),
    )
    builder = EvidenceChainBuilder()
    forward = builder.build_chain(
        proposition="pressure",
        evidence=EvidenceBundle(items=items, has_verified_results=False),
    )
    reverse = builder.build_chain(
        proposition="pressure",
        evidence=EvidenceBundle(items=tuple(reversed(items)), has_verified_results=False),
    )

    assert forward.chain_id == reverse.chain_id
    assert [link.target_id for link in forward.links] == ["ENT-A", "ENT-B"]


def test_reversed_entity_construction_order_produces_identical_graph_digest() -> None:
    """Graph construction must be independent of extraction tuple order."""

    extraction = parse_and_extract(load_golden_document())
    entities = list(extraction.entities or ())
    if len(entities) < 2:
        entities.extend(
            [
                CandidateEntityExtraction(
                    extraction_id="ENT-ORDER-A",
                    document_id=extraction.document_id,
                    extracted_label="Alpha Metric",
                    entity_kind=ExtractedEntityKind.QUANTITY,
                    canonical_entity_type=CanonicalEntityType.QUANTITY,
                    provenance=SourceProvenanceRecord(
                        anchor=ProvenanceReference(
                            document_id=extraction.document_id,
                            page=1,
                        ),
                    ),
                ),
                CandidateEntityExtraction(
                    extraction_id="ENT-ORDER-B",
                    document_id=extraction.document_id,
                    extracted_label="Beta Metric",
                    entity_kind=ExtractedEntityKind.QUANTITY,
                    canonical_entity_type=CanonicalEntityType.QUANTITY,
                    provenance=SourceProvenanceRecord(
                        anchor=ProvenanceReference(
                            document_id=extraction.document_id,
                            page=1,
                        ),
                    ),
                ),
            ],
        )

    registry = build_lox_registry()
    forward = GraphConstructor(registry).construct(
        GraphConstructionBatch(entity_extractions=tuple(entities)),
    )
    reverse = GraphConstructor(registry).construct(
        GraphConstructionBatch(entity_extractions=tuple(reversed(entities))),
    )

    assert canonical_graph_record_digest(forward.store.snapshot()) == (
        canonical_graph_record_digest(reverse.store.snapshot())
    )
