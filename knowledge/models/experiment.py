"""Canonical Experiment model — prediction vs measurement."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace, UncertaintyRecord

__all__ = ("Experiment",)


@dataclass(frozen=True, slots=True, kw_only=True)
class Experiment:
    """Traceable experiment connecting prediction to measured result."""

    experiment_id: str
    objective: str
    hypothesis: str
    test_article: str
    test_configuration: str
    instrumentation: tuple[str, ...]
    input_conditions: str
    measured_quantities: tuple[str, ...]
    procedure: str
    results: str
    provenance: ProvenanceTrace
    uncertainties: tuple[UncertaintyRecord, ...] = ()
    anomalies: str | None = None
    operator: str | None = None
    date: str | None = None
    validation_conclusion: str | None = None
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE

    def __post_init__(self) -> None:
        if not self.experiment_id.strip() or not self.objective.strip():
            raise ValueError("experiment_id and objective are required.")
