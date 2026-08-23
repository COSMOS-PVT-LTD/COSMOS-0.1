"""Unit tests for knowledge.search."""

from __future__ import annotations

import pytest

from knowledge.extraction import (
    CandidateEntityExtraction,
    ExtractedEntityKind,
)
from knowledge.graph import (
    GraphConstructionBatch,
    GraphConstructor,
    GraphQueryService,
    ProvenanceReference,
)
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.indexing import KnowledgeIndexBuilder
from knowledge.ontology import OntologyRegistry
from knowledge.search import (
    KnowledgeSearchEngine,
    NO_VERIFIED_RESULT,
    RetrievalMode,
    SearchQuery,
    SearchValidationError,
)


def _provenance() -> SourceProvenanceRecord:
    return SourceProvenanceRecord(
        anchor=ProvenanceReference(document_id="DOC-001", page=1),
    )


def _engine() -> KnowledgeSearchEngine:
    entity = CandidateEntityExtraction(
        extraction_id="ENT-PC",
        document_id="DOC-001",
        extracted_label="Chamber Pressure",
        entity_kind=ExtractedEntityKind.QUANTITY,
        canonical_entity_type=CanonicalEntityType.QUANTITY,
        provenance=_provenance(),
    )

    result = GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(entity_extractions=(entity,)),
    )
    bundle = KnowledgeIndexBuilder().build(result.store)

    return KnowledgeSearchEngine(
        bundle,
        GraphQueryService(result.store),
        result.store,
    )


def test_search_engine_lexical_mode() -> None:
    """Lexical search must return deterministic matches."""

    engine = _engine()
    page = engine.search(
        SearchQuery(text="chamber pressure", mode=RetrievalMode.LEXICAL),
    )

    assert page.total_count == 1
    assert page.results[0].target_id == "ENT-PC"


def test_search_engine_hybrid_mode_is_deterministic() -> None:
    """Hybrid search must return stable ordering across repeated calls."""

    engine = _engine()
    query = SearchQuery(text="chamber", mode=RetrievalMode.HYBRID)

    first = engine.search(query)
    second = engine.search(query)

    assert [item.target_id for item in first.results] == [
        item.target_id for item in second.results
    ]


def test_search_engine_rejects_invalid_limit() -> None:
    """Search queries must enforce bounded retrieval."""

    with pytest.raises(SearchValidationError):
        SearchQuery(text="chamber", limit=0)


def test_search_engine_empty_result_behavior() -> None:
    """No matches must return an explicit empty page."""

    engine = _engine()
    page = engine.search(
        SearchQuery(text="nonexistent-term-xyz", mode=RetrievalMode.LEXICAL),
    )

    assert page.total_count == 0
    assert page.results == ()
    assert engine.no_verified_result() == NO_VERIFIED_RESULT
