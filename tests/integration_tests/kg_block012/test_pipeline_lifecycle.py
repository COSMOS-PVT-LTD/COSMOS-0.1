"""Lifecycle continuity verification for KG-BLOCK-012."""

from __future__ import annotations

from knowledge.extraction import (
    CandidateEntityExtraction,
    ExtractedEntityKind,
)
from knowledge.graph import GraphLifecycleState, ProvenanceReference
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.reasoning.evidence import EvidenceBundle, EvidenceItem, RankingMetadata
from knowledge.reasoning.w10 import EvidenceClassification, W10ProvenanceAwareReasoner

from tests.integration_tests.kg_block012.helpers.pipeline import run_full_pipeline


def test_candidate_lifecycle_not_promoted_by_pipeline() -> None:
    """Retrieved candidates must not be promoted to approved by the pipeline."""

    artifacts = run_full_pipeline()

    for node in artifacts.store.list_nodes():
        assert node.properties.get("lifecycle_state") != GraphLifecycleState.APPROVED.value

    for item in artifacts.rag_result.context.evidence.items:
        if item.lifecycle_state is not None:
            assert item.lifecycle_state in {
                GraphLifecycleState.CANDIDATE.value,
                GraphLifecycleState.EXTRACTED.value,
                GraphLifecycleState.REVIEWED.value,
            }


def test_candidate_only_reasoning_is_partially_supported() -> None:
    """Candidate-only evidence must not classify as SUPPORTED."""

    item = EvidenceItem(
        target_id="ENT-CAND",
        target_type="Quantity",
        document_id="DOC-001",
        lifecycle_state=GraphLifecycleState.CANDIDATE.value,
        provenance={"document_id": "DOC-001"},
        ranking=RankingMetadata(
            rank=1,
            score=1.0,
            ranking_reason="test",
            tie_breaker="ENT-CAND",
        ),
    )
    outcome = W10ProvenanceAwareReasoner().assess(
        EvidenceBundle(items=(item,), has_verified_results=False),
    )

    assert outcome.classification is EvidenceClassification.PARTIALLY_SUPPORTED


def test_rejected_lifecycle_surfaces_as_unsupported() -> None:
    """Rejected lifecycle must not be treated as supported evidence."""

    from knowledge.reasoning.w10 import W10ProvenanceAwareReasoner

    item = EvidenceItem(
        target_id="ENT-REJ",
        target_type="Quantity",
        document_id="DOC-001",
        lifecycle_state=GraphLifecycleState.REJECTED.value,
        provenance={"document_id": "DOC-001"},
        ranking=RankingMetadata(
            rank=1,
            score=1.0,
            ranking_reason="test",
            tie_breaker="ENT-REJ",
        ),
    )
    reasoner = W10ProvenanceAwareReasoner()

    assert reasoner.classify_item(item) is EvidenceClassification.UNSUPPORTED


def test_conflicted_evidence_surfaces_explicitly() -> None:
    """Conflict visibility must surface CONFLICTED classification."""

    item = EvidenceItem(
        target_id="ENT-CONF",
        target_type="Quantity",
        document_id="DOC-001",
        lifecycle_state=GraphLifecycleState.APPROVED.value,
        provenance={
            "document_id": "DOC-001",
            "conflict_visibility": "CONFIRMED_CONFLICT",
        },
        ranking=RankingMetadata(
            rank=1,
            score=1.0,
            ranking_reason="test",
            tie_breaker="ENT-CONF",
        ),
    )
    outcome = W10ProvenanceAwareReasoner().assess(
        EvidenceBundle(items=(item,), has_verified_results=False),
    )

    assert outcome.classification is EvidenceClassification.CONFLICTED


def test_mixed_lifecycle_extra_entity_remains_candidate() -> None:
    """Synthetic extra entities must enter graph as candidates only."""

    extra = CandidateEntityExtraction(
        extraction_id="ENT-EXTRA",
        document_id="DOC-EXTRA",
        extracted_label="Nozzle Area",
        entity_kind=ExtractedEntityKind.QUANTITY,
        canonical_entity_type=CanonicalEntityType.QUANTITY,
        provenance=SourceProvenanceRecord(
            anchor=ProvenanceReference(document_id="DOC-EXTRA", page=1),
        ),
    )
    artifacts = run_full_pipeline(extra_entities=(extra,))

    extra_nodes = [
        node
        for node in artifacts.store.list_nodes()
        if node.node_id == "ENT-EXTRA"
    ]
    if extra_nodes:
        assert extra_nodes[0].properties.get("lifecycle_state") == (
            GraphLifecycleState.CANDIDATE.value
        )
