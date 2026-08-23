"""Provenance-aware reasoning for KG-045."""

from __future__ import annotations

from knowledge.reasoning.evidence import EvidenceBundle, EvidenceItem
from knowledge.reasoning.exceptions import ReasoningValidationError
from knowledge.reasoning.reasoner import ProvenanceAwareReasoner
from knowledge.reasoning.w10.chains import EvidenceChainBuilder
from knowledge.reasoning.w10.classification import classify_evidence_item
from knowledge.reasoning.w10.models import EvidenceClassification, ReasoningOutcome
from knowledge.search.contracts import NO_VERIFIED_RESULT

__all__ = (
    "W10ProvenanceAwareReasoner",
)


class W10ProvenanceAwareReasoner:
    """W10 provenance-aware reasoning over retrieval evidence."""

    def __init__(self) -> None:
        self._base_reasoner = ProvenanceAwareReasoner()
        self._chain_builder = EvidenceChainBuilder(classify_evidence_item)

    def assess(self, evidence: EvidenceBundle) -> ReasoningOutcome:
        """Assess evidence and produce a deterministic W10 reasoning outcome."""

        if not isinstance(evidence, EvidenceBundle):
            raise ReasoningValidationError(
                "evidence must be an EvidenceBundle instance.",
            )

        if not evidence.items:
            return ReasoningOutcome(
                classification=EvidenceClassification.NO_VERIFIED_RESULT,
                supported_target_ids=(),
                candidate_target_ids=(),
                conflict_target_ids=(),
                chains=(),
                uncertainty_note=NO_VERIFIED_RESULT,
            )

        base = self._base_reasoner.assess(evidence)
        chains = self._chain_builder.build_chains(
            proposition="engineering-proposition",
            evidence=evidence,
        )

        if base.conflict_target_ids:
            classification = EvidenceClassification.CONFLICTED
        elif base.supported_target_ids and base.candidate_target_ids:
            classification = EvidenceClassification.PARTIALLY_SUPPORTED
        elif base.supported_target_ids:
            classification = EvidenceClassification.SUPPORTED
        elif base.candidate_target_ids:
            classification = EvidenceClassification.PARTIALLY_SUPPORTED
        else:
            classification = EvidenceClassification.UNSUPPORTED

        uncertainty_note = None

        if classification is EvidenceClassification.PARTIALLY_SUPPORTED:
            uncertainty_note = (
                "Evidence includes candidate-only or mixed lifecycle support."
            )
        elif classification is EvidenceClassification.UNSUPPORTED:
            uncertainty_note = "No supported or candidate evidence classification."

        return ReasoningOutcome(
            classification=classification,
            supported_target_ids=base.supported_target_ids,
            candidate_target_ids=base.candidate_target_ids,
            conflict_target_ids=base.conflict_target_ids,
            chains=chains,
            uncertainty_note=uncertainty_note,
        )

    def classify_item(self, item: EvidenceItem) -> EvidenceClassification:
        """Return deterministic evidence classification for a single item."""

        return classify_evidence_item(item)
