"""
COSMOS Knowledge Foundation

Module:
    knowledge.reasoning.context

Purpose:
    Compact engineering-context packages for future AI consumers.
"""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.reasoning.evidence import EvidenceBundle
from knowledge.reasoning.exceptions import ReasoningValidationError
from knowledge.reasoning.reasoner import ProvenanceAwareReasoner, ReasoningAssessment
from knowledge.search.contracts import NO_VERIFIED_RESULT, SearchQuery
from knowledge.search.exceptions import ContextAssemblyError

__all__ = (
    "EngineeringContextPackage",
    "EngineeringContextAssembler",
)

_MAX_CONTEXT_EVIDENCE_ITEMS = 1000


@dataclass(frozen=True, slots=True, kw_only=True)
class EngineeringContextPackage:
    """
    Compact context package for downstream AI or development workflows.

    Does not invent facts or remove provenance.
    """

    task: str
    query: SearchQuery
    evidence: EvidenceBundle
    assessment: ReasoningAssessment
    retrieval_metadata: dict[str, object]

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "task": self.task,
            "query": {
                "text": self.query.text,
                "mode": self.query.mode.value,
                "limit": self.query.limit,
                "offset": self.query.offset,
            },
            "evidence": self.evidence.to_mapping(),
            "assessment": self.assessment.to_mapping(),
            "retrieval_metadata": self.retrieval_metadata,
            "no_verified_result": (
                None
                if self.evidence.has_verified_results
                else NO_VERIFIED_RESULT
            ),
        }


class EngineeringContextAssembler:
    """Assemble bounded reasoning context packages from evidence."""

    def __init__(self, reasoner: ProvenanceAwareReasoner) -> None:
        self._reasoner = reasoner

    def assemble(
        self,
        *,
        task: str,
        query: SearchQuery,
        evidence: EvidenceBundle,
        retrieval_metadata: dict[str, object] | None = None,
    ) -> EngineeringContextPackage:
        """Assemble a compact engineering context package."""

        if not isinstance(task, str) or not task.strip():
            raise ReasoningValidationError("task must not be blank.")

        if not isinstance(query, SearchQuery):
            raise ReasoningValidationError(
                "query must be a SearchQuery instance."
            )

        if not isinstance(evidence, EvidenceBundle):
            raise ReasoningValidationError(
                "evidence must be an EvidenceBundle instance."
            )

        if len(evidence.items) > _MAX_CONTEXT_EVIDENCE_ITEMS:
            raise ReasoningValidationError(
                "evidence exceeds maximum context evidence bound."
            )

        assessment = self._reasoner.assess(evidence)

        metadata = dict(retrieval_metadata or {})

        if "result_count" not in metadata:
            metadata["result_count"] = len(evidence.items)

        if not evidence.has_retrieval_results:
            if assessment.unsupported_claim != NO_VERIFIED_RESULT:
                raise ContextAssemblyError(
                    "Evidence bundle must expose NO VERIFIED RESULT sentinel."
                )

        return EngineeringContextPackage(
            task=task.strip(),
            query=query,
            evidence=evidence,
            assessment=assessment,
            retrieval_metadata=metadata,
        )
