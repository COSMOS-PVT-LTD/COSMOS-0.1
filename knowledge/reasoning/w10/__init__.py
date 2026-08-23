"""Public exports for knowledge.reasoning.w10 (KG-BLOCK-011 W10)."""

from __future__ import annotations

from knowledge.reasoning.w10.chains import EvidenceChainBuilder
from knowledge.reasoning.w10.classification import classify_evidence_item
from knowledge.reasoning.w10.context import (
    W10EngineeringContext,
    W10EngineeringContextBuilder,
)
from knowledge.reasoning.w10.identity import (
    deterministic_chain_id,
    deterministic_chain_link_id,
    deterministic_context_digest,
)
from knowledge.reasoning.w10.models import (
    EvidenceChain,
    EvidenceChainLink,
    EvidenceClassification,
    ReasoningOutcome,
)
from knowledge.reasoning.w10.reasoner import W10ProvenanceAwareReasoner

__all__ = (
    "EvidenceChain",
    "EvidenceChainBuilder",
    "EvidenceChainLink",
    "EvidenceClassification",
    "ReasoningOutcome",
    "W10EngineeringContext",
    "W10EngineeringContextBuilder",
    "W10ProvenanceAwareReasoner",
    "classify_evidence_item",
    "deterministic_chain_id",
    "deterministic_chain_link_id",
    "deterministic_context_digest",
)
