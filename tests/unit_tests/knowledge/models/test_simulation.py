"""Simulation model tests."""

from __future__ import annotations

from knowledge.models.lifecycle import ProvenanceTrace
from knowledge.models.simulation import Simulation


def test_simulation_binds_boundary_conditions() -> None:
    simulation = Simulation(
        simulation_id="SIM-1",
        solver="cfd",
        physics_model="RANS",
        geometry="axisymmetric",
        boundary_condition_ids=("BC-1",),
        provenance=ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1"),
        software_version="local",
    )
    assert simulation.boundary_condition_ids == ("BC-1",)
