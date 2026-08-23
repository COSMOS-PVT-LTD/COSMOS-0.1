"""W11 interface models for KG-BLOCK-011."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.interface.exceptions import InterfaceValidationError
from knowledge.reasoning.w10.models import EvidenceClassification, ReasoningOutcome
from knowledge.reasoning.w10.context import W10EngineeringContext
from knowledge.search.contracts import SearchQuery

__all__ = (
    "ContextPackage",
    "ControlledRAGRequest",
    "ControlledRAGResult",
    "CursorDevelopmentContext",
    "EngineeringKnowledgePayload",
)


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise InterfaceValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise InterfaceValidationError(f"{field_name} must not be blank.")

    return cleaned


@dataclass(frozen=True, slots=True, kw_only=True)
class ControlledRAGRequest:
    """Controlled RAG request contract for KG-048."""

    request_id: str
    task: str
    query: SearchQuery
    allowed_document_ids: tuple[str, ...] = ()
    max_results: int = 50

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "request_id",
            _validate_non_empty_string("request_id", self.request_id),
        )
        object.__setattr__(
            self,
            "task",
            _validate_non_empty_string("task", self.task),
        )

        if not isinstance(self.query, SearchQuery):
            raise InterfaceValidationError(
                "query must be a SearchQuery instance.",
            )

        if not isinstance(self.max_results, int) or isinstance(self.max_results, bool):
            raise InterfaceValidationError("max_results must be an integer.")

        if self.max_results <= 0 or self.max_results > 1000:
            raise InterfaceValidationError(
                "max_results must be between 1 and 1000.",
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ControlledRAGResult:
    """Controlled RAG result without autonomous model invocation."""

    request: ControlledRAGRequest
    context: W10EngineeringContext
    retrieval_methods: tuple[str, ...]
    package_digest: str
    provider_invoked: bool = False

    @property
    def request_id(self) -> str:
        return self.request.request_id

    def to_mapping(self) -> dict[str, object]:
        return {
            "request_id": self.request.request_id,
            "context": self.context.to_mapping(),
            "retrieval_methods": list(self.retrieval_methods),
            "package_digest": self.package_digest,
            "provider_invoked": self.provider_invoked,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextPackage:
    """Stable context package for downstream consumers (KG-049)."""

    package_id: str
    package_version: str
    request: ControlledRAGRequest
    result: ControlledRAGResult
    classification: EvidenceClassification
    package_digest: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "package_id": self.package_id,
            "package_version": self.package_version,
            "request": {
                "request_id": self.request.request_id,
                "task": self.request.task,
            },
            "result": self.result.to_mapping(),
            "classification": self.classification.value,
            "package_digest": self.package_digest,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class CursorDevelopmentContext:
    """Cursor development context boundary for KG-050."""

    context_id: str
    project_id: str
    engineering_task_id: str
    package: ContextPackage
    constraints: tuple[str, ...]
    assumptions: tuple[str, ...]
    content_kind: str = "knowledge_evidence"
    context_digest: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "context_id": self.context_id,
            "project_id": self.project_id,
            "engineering_task_id": self.engineering_task_id,
            "package": self.package.to_mapping(),
            "constraints": list(self.constraints),
            "assumptions": list(self.assumptions),
            "content_kind": self.content_kind,
            "context_digest": self.context_digest,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class EngineeringKnowledgePayload:
    """Knowledge-to-engineering interface payload for KG-051."""

    payload_id: str
    cursor_context: CursorDevelopmentContext
    outcome: ReasoningOutcome
    lifecycle_preserved: bool
    provenance_preserved: bool
    payload_digest: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "payload_id": self.payload_id,
            "cursor_context": self.cursor_context.to_mapping(),
            "outcome": self.outcome.to_mapping(),
            "lifecycle_preserved": self.lifecycle_preserved,
            "provenance_preserved": self.provenance_preserved,
            "payload_digest": self.payload_digest,
        }
