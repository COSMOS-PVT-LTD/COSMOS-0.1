"""Canonical Simulation model."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace, UncertaintyRecord

__all__ = ("Simulation",)


@dataclass(frozen=True, slots=True, kw_only=True)
class Simulation:
    """Traceable simulation case bound to solver, BCs, and software version."""

    simulation_id: str
    solver: str
    physics_model: str
    geometry: str
    boundary_condition_ids: tuple[str, ...]
    provenance: ProvenanceTrace
    mesh: str | None = None
    initial_conditions: str | None = None
    material_model_ids: tuple[str, ...] = ()
    numerical_scheme: str | None = None
    convergence_criteria: str | None = None
    inputs: str | None = None
    outputs: str | None = None
    uncertainty: UncertaintyRecord | None = None
    software_version: str | None = None
    verification_status: str = "UNREVIEWED"
    validation_status: str = "UNREVIEWED"
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE

    def __post_init__(self) -> None:
        if not self.simulation_id.strip() or not self.solver.strip():
            raise ValueError("simulation_id and solver are required.")
