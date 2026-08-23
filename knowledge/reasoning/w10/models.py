"""W10 reasoning models for KG-BLOCK-011."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.reasoning.exceptions import ReasoningValidationError

__all__ = (
    "EvidenceChain",
    "EvidenceChainLink",
    "EvidenceClassification",
    "ReasoningOutcome",
)


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ReasoningValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise ReasoningValidationError(f"{field_name} must not be blank.")

    return cleaned


class EvidenceClassification(Enum):
    """Deterministic evidence classification taxonomy for W10 reasoning."""

    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONFLICTED = "CONFLICTED"
    NO_VERIFIED_RESULT = "NO_VERIFIED_RESULT"


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceChainLink:
    """Single link in a provenance-preserving evidence chain."""

    link_id: str
    target_id: str
    target_type: str
    document_id: str | None
    lifecycle_state: str | None
    provenance: dict[str, object]
    classification: EvidenceClassification
    confidence: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "link_id",
            _validate_non_empty_string("link_id", self.link_id),
        )
        object.__setattr__(
            self,
            "target_id",
            _validate_non_empty_string("target_id", self.target_id),
        )
        object.__setattr__(
            self,
            "target_type",
            _validate_non_empty_string("target_type", self.target_type),
        )

        if not isinstance(self.provenance, dict):
            raise ReasoningValidationError("provenance must be a dict.")

        if self.confidence is not None:
            if not isinstance(self.confidence, (int, float)) or isinstance(
                self.confidence,
                bool,
            ):
                raise ReasoningValidationError("confidence must be a number.")

            confidence = float(self.confidence)

            if confidence < 0.0 or confidence > 1.0:
                raise ReasoningValidationError(
                    "confidence must be between 0.0 and 1.0.",
                )

            object.__setattr__(self, "confidence", confidence)

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "link_id": self.link_id,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "classification": self.classification.value,
            "provenance": self.provenance,
        }

        if self.document_id is not None:
            payload["document_id"] = self.document_id
        if self.lifecycle_state is not None:
            payload["lifecycle_state"] = self.lifecycle_state
        if self.confidence is not None:
            payload["confidence"] = self.confidence

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceChain:
    """Inspectable evidence chain for KG-046."""

    chain_id: str
    proposition: str
    links: tuple[EvidenceChainLink, ...]
    has_conflict: bool = False
    missing_source: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "chain_id",
            _validate_non_empty_string("chain_id", self.chain_id),
        )
        object.__setattr__(
            self,
            "proposition",
            _validate_non_empty_string("proposition", self.proposition),
        )

        if not isinstance(self.links, tuple):
            raise ReasoningValidationError("links must be a tuple.")

        link_ids = [link.link_id for link in self.links]

        if len(link_ids) != len(set(link_ids)):
            raise ReasoningValidationError(
                "Evidence chain contains duplicate link identifiers.",
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "proposition": self.proposition,
            "links": [link.to_mapping() for link in self.links],
            "has_conflict": self.has_conflict,
            "missing_source": self.missing_source,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ReasoningOutcome:
    """Deterministic W10 reasoning outcome for KG-045."""

    classification: EvidenceClassification
    supported_target_ids: tuple[str, ...]
    candidate_target_ids: tuple[str, ...]
    conflict_target_ids: tuple[str, ...]
    chains: tuple[EvidenceChain, ...]
    uncertainty_note: str | None = None

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "classification": self.classification.value,
            "supported_target_ids": list(self.supported_target_ids),
            "candidate_target_ids": list(self.candidate_target_ids),
            "conflict_target_ids": list(self.conflict_target_ids),
            "chains": [chain.to_mapping() for chain in self.chains],
        }

        if self.uncertainty_note is not None:
            payload["uncertainty_note"] = self.uncertainty_note

        return payload
