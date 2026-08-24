"""BoundaryCondition model tests."""

from __future__ import annotations

from knowledge.models.boundary_condition import BoundaryCondition
from knowledge.models.lifecycle import ProvenanceTrace


def test_boundary_condition_is_solver_bound() -> None:
    boundary = BoundaryCondition(
        boundary_condition_id="BC-1",
        name="wall heat flux",
        quantity="heat_flux",
        value_expression="q_wall",
        unit="W/m^2",
        geometry_location="chamber wall",
        applicable_solver="thermal",
        applicable_physics="conjugate heat transfer",
        provenance=ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1"),
    )
    assert boundary.applicable_solver == "thermal"
