"""Simulation candidate extractor."""

from __future__ import annotations

from knowledge.extraction.candidate import candidate_provenance
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.models.simulation import Simulation

__all__ = ("extract_simulations",)


def extract_simulations(
    text: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[Simulation, ...]:
    if "cfd" not in text.lower() and "simulation" not in text.lower():
        return ()
    return (
        Simulation(
            simulation_id="SIM-CAND-000",
            solver="UNSPECIFIED",
            physics_model="unreviewed",
            geometry="unreviewed",
            boundary_condition_ids=(),
            provenance=candidate_provenance(document_id, reference_id),
            lifecycle=KnowledgeLifecycle.CANDIDATE,
        ),
    )
