"""Unit tests for knowledge.reasoning."""

from __future__ import annotations

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
from knowledge.reasoning import (
    EngineeringContextAssembler,
    EvidenceRanker,
    ProvenanceAwareReasoner,
)
from knowledge.search import KnowledgeSearchEngine, RetrievalMode, SearchQuery
from knowledge.search.contracts import NO_VERIFIED_RESULT


def _provenance() -> SourceProvenanceRecord:
    return SourceProvenanceRecord(
        anchor=ProvenanceReference(document_id="DOC-001", page=1),
    )


def _pipeline():
    entity = CandidateEntityExtraction(
        extraction_id="ENT-PC",
        document_id="DOC-001",
        extracted_label="Chamber Pressure",
        entity_kind=ExtractedEntityKind.QUANTITY,
        canonical_entity_type=CanonicalEntityType.QUANTITY,
        provenance=_provenance(),
    )

    graph_result = GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(entity_extractions=(entity,)),
    )
    store = graph_result.store
    graph_query = GraphQueryService(store)
    bundle = KnowledgeIndexBuilder().build(store)
    engine = KnowledgeSearchEngine(bundle, graph_query, store)

    return engine, graph_query


def test_evidence_ranker_assembles_provenance() -> None:
    """Evidence assembly must retain provenance and ranking metadata."""

    engine, graph_query = _pipeline()
    page = engine.search(
        SearchQuery(text="chamber", mode=RetrievalMode.LEXICAL),
    )

    bundle = EvidenceRanker(graph_query).assemble(page.results)

    assert bundle.has_retrieval_results
    assert not bundle.has_verified_results
    assert len(bundle.items) == 1
    assert bundle.items[0].provenance["document_id"] == "DOC-001"
    assert bundle.items[0].ranking.rank == 1


def test_provenance_aware_reasoner_preserves_candidate_state() -> None:
    """Reasoning must not upgrade candidates to supported facts."""

    engine, graph_query = _pipeline()
    page = engine.search(
        SearchQuery(text="chamber", mode=RetrievalMode.LEXICAL),
    )
    evidence = EvidenceRanker(graph_query).assemble(page.results)

    assessment = ProvenanceAwareReasoner().assess(evidence)

    assert assessment.supported_target_ids == ()
    assert assessment.candidate_target_ids == ("ENT-PC",)


def test_engineering_context_package_is_deterministic() -> None:
    """Context packages must assemble bounded evidence for AI consumers."""

    engine, graph_query = _pipeline()
    query = SearchQuery(text="chamber", mode=RetrievalMode.HYBRID)
    page = engine.search(query)
    evidence = EvidenceRanker(graph_query).assemble(page.results)

    package = EngineeringContextAssembler(
        ProvenanceAwareReasoner(),
    ).assemble(
        task="Review chamber pressure entity",
        query=query,
        evidence=evidence,
        retrieval_metadata={"mode": query.mode.value},
    )

    mapping = package.to_mapping()

    assert mapping["task"] == "Review chamber pressure entity"
    assert mapping["evidence"]["has_retrieval_results"] is True
    assert mapping["evidence"]["has_verified_results"] is False
    assert mapping["no_verified_result"] == NO_VERIFIED_RESULT


def test_empty_evidence_reports_no_verified_result() -> None:
    """Empty evidence must surface the explicit no-verified-result sentinel."""

    assessment = ProvenanceAwareReasoner().assess(
        EvidenceRanker(
            _pipeline()[1],
        ).assemble(()),
    )

    assert assessment.unsupported_claim == NO_VERIFIED_RESULT
