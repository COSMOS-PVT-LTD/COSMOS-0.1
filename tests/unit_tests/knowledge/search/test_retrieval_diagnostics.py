"""Step 6 retrieval diagnostics tests."""

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
from knowledge.indexing.w7 import W7IndexBuilder
from knowledge.ontology import OntologyRegistry
from knowledge.search import RetrievalMode, SearchQuery
from knowledge.search.retrieval_diagnostics import build_retrieval_diagnostics
from knowledge.search.w8.hybrid import HybridSearchEngine


def _build_hybrid_page():
    entity = CandidateEntityExtraction(
        extraction_id="ENT-1",
        document_id="DOC-001",
        extracted_label="Chamber Pressure",
        entity_kind=ExtractedEntityKind.QUANTITY,
        canonical_entity_type=CanonicalEntityType.QUANTITY,
        provenance=SourceProvenanceRecord(
            anchor=ProvenanceReference(document_id="DOC-001", page=1),
        ),
    )
    store = GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(entity_extractions=(entity,)),
    ).store
    bundle = W7IndexBuilder().build(store)
    graph_query = GraphQueryService(store)
    engine = HybridSearchEngine(bundle, graph_query, store)
    query = SearchQuery(text="chamber pressure", mode=RetrievalMode.HYBRID)
    return query, engine.search(query)


def test_build_retrieval_diagnostics_includes_ranking_reason() -> None:
    """Retrieval diagnostics must expose ranking reasons and scores."""

    query, page = _build_hybrid_page()
    diagnostics = build_retrieval_diagnostics(query, page)

    assert diagnostics.returned_count >= 1
    assert diagnostics.entries[0].ranking_reason
    assert diagnostics.entries[0].target_id


def test_build_retrieval_diagnostics_is_deterministic() -> None:
    """Retrieval diagnostics must be deterministic."""

    query, page = _build_hybrid_page()
    first = build_retrieval_diagnostics(query, page)
    second = build_retrieval_diagnostics(query, page)

    assert first.report_digest == second.report_digest
