"""Evidence classification helpers for W10 reasoning."""

from __future__ import annotations

from knowledge.graph.lifecycle import GraphLifecycleState
from knowledge.reasoning.evidence import EvidenceItem
from knowledge.reasoning.w10.models import EvidenceClassification

__all__ = (
    "classify_evidence_item",
)


def classify_evidence_item(item: EvidenceItem) -> EvidenceClassification:
    """Return deterministic evidence classification for a single item."""

    conflict_visibility = item.provenance.get("conflict_visibility")

    if conflict_visibility == "CONFIRMED_CONFLICT":
        return EvidenceClassification.CONFLICTED

    if conflict_visibility == "POTENTIAL_CONFLICT":
        return EvidenceClassification.PARTIALLY_SUPPORTED

    lifecycle = item.lifecycle_state

    if lifecycle in {
        GraphLifecycleState.REJECTED.value,
        GraphLifecycleState.DEPRECATED.value,
    }:
        return EvidenceClassification.UNSUPPORTED

    if lifecycle == GraphLifecycleState.APPROVED.value:
        return EvidenceClassification.SUPPORTED

    if lifecycle in {
        GraphLifecycleState.CANDIDATE.value,
        GraphLifecycleState.EXTRACTED.value,
        GraphLifecycleState.REVIEWED.value,
    }:
        return EvidenceClassification.PARTIALLY_SUPPORTED

    return EvidenceClassification.UNSUPPORTED
