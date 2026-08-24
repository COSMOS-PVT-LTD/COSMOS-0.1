"""Canonical FailureMode model."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace

__all__ = ("FailureMode",)


@dataclass(frozen=True, slots=True, kw_only=True)
class FailureMode:
    """Failure mechanism with cause, effect, mitigation, and design-rule link."""

    failure_mode_id: str
    name: str
    mechanism: str
    cause: str
    effect: str
    severity: str
    likelihood: str
    mitigation: str
    provenance: ProvenanceTrace
    detectability: str | None = None
    design_rule_ids: tuple[str, ...] = ()
    test_method: str | None = None
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE
    validation_status: str = "UNREVIEWED"

    def __post_init__(self) -> None:
        if not self.failure_mode_id.strip() or not self.name.strip():
            raise ValueError("failure_mode_id and name are required.")
        if not self.mechanism.strip():
            raise ValueError("mechanism is required.")
