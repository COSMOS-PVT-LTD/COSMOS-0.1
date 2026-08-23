"""
COSMOS Knowledge Foundation

Module:
    knowledge.reasoning.reasoner

Purpose:
    Provenance-aware deterministic reasoning over retrieval evidence.
"""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.graph.lifecycle import GraphLifecycleState
from knowledge.reasoning.evidence import EvidenceBundle, EvidenceItem
from knowledge.reasoning.exceptions import ReasoningValidationError
from knowledge.search.contracts import NO_VERIFIED_RESULT

__all__ = (
    "ProvenanceAwareReasoner",
    "ReasoningAssessment",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ReasoningAssessment:
    """Deterministic reasoning assessment over assembled evidence."""

    supported_target_ids: tuple[str, ...]
    candidate_target_ids: tuple[str, ...]
    conflict_target_ids: tuple[str, ...]
    unsupported_claim: str | None = None

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "supported_target_ids": list(self.supported_target_ids),
            "candidate_target_ids": list(self.candidate_target_ids),
            "conflict_target_ids": list(self.conflict_target_ids),
        }

        if self.unsupported_claim is not None:
            payload["unsupported_claim"] = self.unsupported_claim

        return payload


class ProvenanceAwareReasoner:
    """
    Deterministic provenance-aware reasoning over retrieval evidence.

    Does not approve knowledge or perform engineering calculations.
    """

    def assess(self, evidence: EvidenceBundle) -> ReasoningAssessment:
        """Assess evidence without upgrading lifecycle or confidence."""

        if not isinstance(evidence, EvidenceBundle):
            raise ReasoningValidationError(
                "evidence must be an EvidenceBundle instance."
            )

        if not evidence.items:
            return ReasoningAssessment(
                supported_target_ids=(),
                candidate_target_ids=(),
                conflict_target_ids=(),
                unsupported_claim=NO_VERIFIED_RESULT,
            )

        supported: list[str] = []
        candidates: list[str] = []
        conflicts: list[str] = []

        for item in evidence.items:
            lifecycle = item.lifecycle_state
            conflict_visibility = item.provenance.get("conflict_visibility")

            if conflict_visibility == "CONFIRMED_CONFLICT":
                conflicts.append(item.target_id)
                continue

            if lifecycle == GraphLifecycleState.APPROVED.value:
                supported.append(item.target_id)
            else:
                candidates.append(item.target_id)

        return ReasoningAssessment(
            supported_target_ids=tuple(sorted(supported)),
            candidate_target_ids=tuple(sorted(candidates)),
            conflict_target_ids=tuple(sorted(conflicts)),
        )

    def classify_item(self, item: EvidenceItem) -> str:
        """Return a deterministic evidence classification label."""

        if item.provenance.get("conflict_visibility") == "CONFIRMED_CONFLICT":
            return "confirmed_conflict"

        lifecycle = item.lifecycle_state

        if lifecycle == GraphLifecycleState.APPROVED.value:
            return "supported"

        if lifecycle in {
            GraphLifecycleState.CANDIDATE.value,
            GraphLifecycleState.EXTRACTED.value,
        }:
            return "candidate"

        return "unknown"
