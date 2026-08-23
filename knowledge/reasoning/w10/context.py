"""Engineering context builder for KG-047."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.reasoning.evidence import EvidenceBundle
from knowledge.reasoning.exceptions import ReasoningValidationError
from knowledge.reasoning.w10.identity import deterministic_context_digest
from knowledge.reasoning.w10.models import EvidenceClassification, ReasoningOutcome
from knowledge.reasoning.w10.reasoner import W10ProvenanceAwareReasoner
from knowledge.search.contracts import NO_VERIFIED_RESULT, SearchQuery
from knowledge.search.exceptions import ContextAssemblyError
from knowledge.validation.models import ValidationReport

__all__ = (
    "W10EngineeringContext",
    "W10EngineeringContextBuilder",
)

_MAX_CONTEXT_EVIDENCE_ITEMS = 1000
_MAX_CONTEXT_CHAINS = 500


@dataclass(frozen=True, slots=True, kw_only=True)
class W10EngineeringContext:
    """Bounded engineering context package for KG-047."""

    task: str
    query: SearchQuery
    evidence: EvidenceBundle
    outcome: ReasoningOutcome
    validation_report_digest: str | None
    context_digest: str
    retrieval_metadata: dict[str, object]

    def to_mapping(self) -> dict[str, object]:
        return {
            "task": self.task,
            "query": {
                "text": self.query.text,
                "mode": self.query.mode.value,
                "limit": self.query.limit,
                "offset": self.query.offset,
            },
            "evidence": self.evidence.to_mapping(),
            "outcome": self.outcome.to_mapping(),
            "validation_report_digest": self.validation_report_digest,
            "context_digest": self.context_digest,
            "retrieval_metadata": self.retrieval_metadata,
            "no_verified_result": (
                None
                if self.outcome.classification
                is not EvidenceClassification.NO_VERIFIED_RESULT
                else NO_VERIFIED_RESULT
            ),
        }


class W10EngineeringContextBuilder:
    """Build bounded W10 engineering context from evidence and validation."""

    def __init__(self, reasoner: W10ProvenanceAwareReasoner | None = None) -> None:
        self._reasoner = reasoner or W10ProvenanceAwareReasoner()

    def build(
        self,
        *,
        task: str,
        query: SearchQuery,
        evidence: EvidenceBundle,
        validation_report: ValidationReport | None = None,
        retrieval_metadata: dict[str, object] | None = None,
        max_evidence_items: int = _MAX_CONTEXT_EVIDENCE_ITEMS,
    ) -> W10EngineeringContext:
        """Assemble a bounded engineering context package."""

        if not isinstance(task, str) or not task.strip():
            raise ReasoningValidationError("task must not be blank.")

        if not isinstance(query, SearchQuery):
            raise ReasoningValidationError(
                "query must be a SearchQuery instance.",
            )

        if not isinstance(evidence, EvidenceBundle):
            raise ReasoningValidationError(
                "evidence must be an EvidenceBundle instance.",
            )

        if len(evidence.items) > max_evidence_items:
            raise ReasoningValidationError(
                "evidence exceeds maximum context evidence bound.",
            )

        outcome = self._reasoner.assess(evidence)

        if len(outcome.chains) > _MAX_CONTEXT_CHAINS:
            raise ReasoningValidationError(
                "evidence chains exceed maximum context chain bound.",
            )

        if not evidence.has_retrieval_results:
            if outcome.classification is not EvidenceClassification.NO_VERIFIED_RESULT:
                raise ContextAssemblyError(
                    "Empty evidence must classify as NO_VERIFIED_RESULT.",
                )

        metadata = dict(retrieval_metadata or {})

        if "result_count" not in metadata:
            metadata["result_count"] = len(evidence.items)

        chain_ids = tuple(chain.chain_id for chain in outcome.chains)
        context_digest = deterministic_context_digest(
            task.strip(),
            query.text,
            outcome.classification.value,
            *chain_ids,
        )

        return W10EngineeringContext(
            task=task.strip(),
            query=query,
            evidence=evidence,
            outcome=outcome,
            validation_report_digest=(
                validation_report.report_digest if validation_report else None
            ),
            context_digest=context_digest,
            retrieval_metadata=metadata,
        )
