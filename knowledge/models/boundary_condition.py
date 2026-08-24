"""Canonical BoundaryCondition — knowledge-to-solver bridge."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace

__all__ = ("BoundaryCondition",)


@dataclass(frozen=True, slots=True, kw_only=True)
class BoundaryCondition:
    """Controlled boundary condition for CFD / thermal / structural solvers."""

    boundary_condition_id: str
    name: str
    quantity: str
    value_expression: str
    unit: str
    geometry_location: str
    applicable_solver: str
    applicable_physics: str
    provenance: ProvenanceTrace
    assumption_ids: tuple[str, ...] = ()
    time_dependence: str = "STEADY"
    phase: str | None = None
    species: str | None = None
    validity: str | None = None
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE
    verification_status: str = "UNREVIEWED"

    def __post_init__(self) -> None:
        if not self.boundary_condition_id.strip() or not self.name.strip():
            raise ValueError("boundary_condition_id and name are required.")
        if not self.quantity.strip() or not self.value_expression.strip():
            raise ValueError("quantity and value_expression are required.")
