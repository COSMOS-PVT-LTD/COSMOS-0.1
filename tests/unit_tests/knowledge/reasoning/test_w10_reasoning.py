"""Unit tests for KG-BLOCK-011 W10 reasoning (KG-045 → KG-047)."""

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
    GraphQueryService,
    ProvenanceReference,
)
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.indexing import KnowledgeIndexBuilder
from knowledge.ontology import OntologyRegistry
from knowledge.reasoning import EvidenceRanker
from knowledge.reasoning.evidence import EvidenceBundle, EvidenceItem, RankingMetadata
from knowledge.reasoning.exceptions import ReasoningValidationError
from knowledge.reasoning.w10 import (
    EvidenceChainBuilder,
    EvidenceClassification,
    W10EngineeringContextBuilder,
    W10ProvenanceAwareReasoner,
    classify_evidence_item,
    deterministic_chain_id,
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


def _evidence_item(
    *,
    target_id: str = "ENT-PC",
    lifecycle_state: str = GraphLifecycleState.CANDIDATE.value,
    conflict_visibility: str | None = None,
) -> EvidenceItem:
    provenance: dict[str, object] = {"document_id": "DOC-001"}

    if conflict_visibility is not None:
        provenance["conflict_visibility"] = conflict_visibility

    return EvidenceItem(
        target_id=target_id,
        target_type="Quantity",
        document_id="DOC-001",
        lifecycle_state=lifecycle_state,
        provenance=provenance,
        ranking=RankingMetadata(
            rank=1,
            score=1.0,
            ranking_reason="test",
            tie_breaker=target_id,
        ),
    )


def test_kg045_candidate_only_evidence_is_partially_supported() -> None:
    """KG-045 must classify candidate evidence as partially supported."""

    evidence = EvidenceBundle(
        items=(_evidence_item(),),
        has_verified_results=False,
    )
    outcome = W10ProvenanceAwareReasoner().assess(evidence)

    assert outcome.classification is EvidenceClassification.PARTIALLY_SUPPORTED
    assert outcome.candidate_target_ids == ("ENT-PC",)
    assert outcome.supported_target_ids == ()


def test_kg045_approved_evidence_is_supported() -> None:
    """KG-045 must classify approved evidence as supported."""

    evidence = EvidenceBundle(
        items=(
            _evidence_item(lifecycle_state=GraphLifecycleState.APPROVED.value),
        ),
        has_verified_results=True,
    )
    outcome = W10ProvenanceAwareReasoner().assess(evidence)

    assert outcome.classification is EvidenceClassification.SUPPORTED
    assert outcome.supported_target_ids == ("ENT-PC",)


def test_kg045_empty_evidence_reports_no_verified_result() -> None:
    """KG-045 must surface NO_VERIFIED_RESULT for empty evidence."""

    outcome = W10ProvenanceAwareReasoner().assess(
        EvidenceBundle(items=(), has_verified_results=False),
    )

    assert outcome.classification is EvidenceClassification.NO_VERIFIED_RESULT
    assert outcome.uncertainty_note == NO_VERIFIED_RESULT


def test_kg045_conflicting_evidence_is_conflicted() -> None:
    """KG-045 must classify confirmed conflicts."""

    evidence = EvidenceBundle(
        items=(
            _evidence_item(conflict_visibility="CONFIRMED_CONFLICT"),
        ),
        has_verified_results=False,
    )
    outcome = W10ProvenanceAwareReasoner().assess(evidence)

    assert outcome.classification is EvidenceClassification.CONFLICTED
    assert outcome.conflict_target_ids == ("ENT-PC",)


def test_kg045_reasoning_does_not_promote_candidate_lifecycle() -> None:
    """KG-045 must not upgrade candidates to approved."""

    item = _evidence_item()
    W10ProvenanceAwareReasoner().assess(
        EvidenceBundle(items=(item,), has_verified_results=False),
    )

    assert item.lifecycle_state == GraphLifecycleState.CANDIDATE.value


def test_kg046_evidence_chain_has_stable_identity() -> None:
    """KG-046 must produce deterministic chain IDs."""

    evidence = EvidenceBundle(
        items=(_evidence_item(),),
        has_verified_results=False,
    )
    builder = EvidenceChainBuilder()

    first = builder.build_chain(proposition="pressure", evidence=evidence)
    second = builder.build_chain(proposition="pressure", evidence=evidence)

    assert first.chain_id == second.chain_id
    assert first.chain_id == deterministic_chain_id("pressure", "ENT-PC")


def test_kg046_chain_preserves_provenance() -> None:
    """KG-046 must preserve provenance in chain links."""

    evidence = EvidenceBundle(
        items=(_evidence_item(),),
        has_verified_results=False,
    )
    chain = EvidenceChainBuilder().build_chain(
        proposition="pressure",
        evidence=evidence,
    )

    assert chain.links[0].provenance["document_id"] == "DOC-001"


def test_kg046_missing_source_is_visible() -> None:
    """KG-046 must mark missing source on empty evidence."""

    chain = EvidenceChainBuilder().build_chain(
        proposition="pressure",
        evidence=EvidenceBundle(items=(), has_verified_results=False),
    )

    assert chain.missing_source is True
    assert chain.links == ()


def test_kg047_context_builder_is_bounded() -> None:
    """KG-047 must reject oversized evidence bundles."""

    items = tuple(
        _evidence_item(target_id=f"ENT-{index}")
        for index in range(1001)
    )

    with pytest.raises(ReasoningValidationError, match="maximum context evidence"):
        W10EngineeringContextBuilder().build(
            task="task",
            query=SearchQuery(text="chamber", mode=RetrievalMode.LEXICAL),
            evidence=EvidenceBundle(items=items, has_verified_results=False),
        )


def test_kg047_context_digest_is_deterministic() -> None:
    """KG-047 must produce stable context digests."""

    engine, graph_query = _pipeline()
    query = SearchQuery(text="chamber", mode=RetrievalMode.LEXICAL)
    page = engine.search(query)
    evidence = EvidenceRanker(graph_query).assemble(page.results)
    builder = W10EngineeringContextBuilder()

    first = builder.build(task="Review pressure", query=query, evidence=evidence)
    second = builder.build(task="Review pressure", query=query, evidence=evidence)

    assert first.context_digest == second.context_digest


def test_kg045_deterministic_reasoning_output() -> None:
    """KG-045 reasoning must be deterministic across repeated runs."""

    engine, graph_query = _pipeline()
    query = SearchQuery(text="chamber", mode=RetrievalMode.LEXICAL)
    evidence = EvidenceRanker(graph_query).assemble(
        engine.search(query).results,
    )
    reasoner = W10ProvenanceAwareReasoner()

    first = reasoner.assess(evidence)
    second = reasoner.assess(evidence)

    assert first.to_mapping() == second.to_mapping()


def test_kg046_duplicate_chain_link_ids_rejected() -> None:
    """KG-046 must reject duplicate link IDs within a chain."""

    from knowledge.reasoning.w10.models import EvidenceChain, EvidenceChainLink

    link = EvidenceChainLink(
        link_id="link-1",
        target_id="ENT-1",
        target_type="Quantity",
        document_id="DOC-001",
        lifecycle_state="CANDIDATE",
        provenance={"document_id": "DOC-001"},
        classification=EvidenceClassification.PARTIALLY_SUPPORTED,
    )

    with pytest.raises(ReasoningValidationError, match="duplicate link"):
        EvidenceChain(
            chain_id="chain-1",
            proposition="pressure",
            links=(link, link),
        )


def test_classify_evidence_item_maps_lifecycle_correctly() -> None:
    """Classification helper must map lifecycle states deterministically."""

    assert (
        classify_evidence_item(_evidence_item())
        is EvidenceClassification.PARTIALLY_SUPPORTED
    )
