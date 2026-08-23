"""Evidence chain construction for KG-046."""

from __future__ import annotations

from collections.abc import Callable

from knowledge.reasoning.evidence import EvidenceBundle
from knowledge.reasoning.evidence import EvidenceItem
from knowledge.reasoning.exceptions import ReasoningValidationError
from knowledge.reasoning.w10.classification import classify_evidence_item
from knowledge.reasoning.w10.identity import (
    deterministic_chain_id,
    deterministic_chain_link_id,
)
from knowledge.reasoning.w10.models import (
    EvidenceChain,
    EvidenceChainLink,
    EvidenceClassification,
)

__all__ = (
    "EvidenceChainBuilder",
)


class EvidenceChainBuilder:
    """Build explicit provenance-preserving evidence chains."""

    def __init__(
        self,
        classifier: Callable[[EvidenceItem], EvidenceClassification] | None = None,
    ) -> None:
        self._classifier = classifier or classify_evidence_item

    def build_chain(
        self,
        *,
        proposition: str,
        evidence: EvidenceBundle,
    ) -> EvidenceChain:
        """Build a deterministic evidence chain from an evidence bundle."""

        if not isinstance(proposition, str) or not proposition.strip():
            raise ReasoningValidationError("proposition must not be blank.")

        if not isinstance(evidence, EvidenceBundle):
            raise ReasoningValidationError(
                "evidence must be an EvidenceBundle instance.",
            )

        if not evidence.items:
            chain_id = deterministic_chain_id(proposition.strip())
            return EvidenceChain(
                chain_id=chain_id,
                proposition=proposition.strip(),
                links=(),
                missing_source=True,
            )

        target_ids = tuple(sorted(item.target_id for item in evidence.items))
        chain_id = deterministic_chain_id(proposition.strip(), *target_ids)
        links: list[EvidenceChainLink] = []
        has_conflict = False
        missing_source = False

        for index, item in enumerate(
            sorted(evidence.items, key=lambda entry: entry.target_id),
        ):
            classification = self._classifier(item)

            if classification is EvidenceClassification.CONFLICTED:
                has_conflict = True

            if item.document_id is None:
                missing_source = True

            confidence_value = item.provenance.get("confidence_score")

            confidence = (
                float(confidence_value)
                if isinstance(confidence_value, (int, float))
                and not isinstance(confidence_value, bool)
                else None
            )

            links.append(
                EvidenceChainLink(
                    link_id=deterministic_chain_link_id(
                        chain_id,
                        item.target_id,
                        index,
                    ),
                    target_id=item.target_id,
                    target_type=item.target_type,
                    document_id=item.document_id,
                    lifecycle_state=item.lifecycle_state,
                    provenance=dict(item.provenance),
                    classification=classification,
                    confidence=confidence,
                ),
            )

        return EvidenceChain(
            chain_id=chain_id,
            proposition=proposition.strip(),
            links=tuple(links),
            has_conflict=has_conflict,
            missing_source=missing_source,
        )

    def build_chains(
        self,
        *,
        proposition: str,
        evidence: EvidenceBundle,
    ) -> tuple[EvidenceChain, ...]:
        """Build one chain per evidence item for inspectable downstream use."""

        if not evidence.items:
            return (self.build_chain(proposition=proposition, evidence=evidence),)

        chains = tuple(
            self.build_chain(
                proposition=f"{proposition}::{item.target_id}",
                evidence=EvidenceBundle(
                    items=(item,),
                    has_verified_results=(
                        item.lifecycle_state == "APPROVED"
                    ),
                ),
            )
            for item in sorted(evidence.items, key=lambda entry: entry.target_id)
        )

        return chains
