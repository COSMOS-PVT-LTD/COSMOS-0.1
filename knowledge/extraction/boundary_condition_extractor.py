"""Boundary-condition candidate extractor — CANDIDATE only."""

from __future__ import annotations

from knowledge.models.boundary_condition import BoundaryCondition
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.extraction.candidate import candidate_provenance

__all__ = ("extract_boundary_conditions",)


def extract_boundary_conditions(
    text: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[BoundaryCondition, ...]:
    if "boundary condition" not in text.lower() and "wall temperature" not in text.lower():
        return ()
    return (
        BoundaryCondition(
            boundary_condition_id="BC-CAND-000",
            name="Extracted wall boundary",
            quantity="temperature",
            value_expression="T_wall",
            unit="K",
            geometry_location="wall",
            applicable_solver="UNSPECIFIED",
            applicable_physics="thermal",
            provenance=candidate_provenance(document_id, reference_id),
            lifecycle=KnowledgeLifecycle.CANDIDATE,
        ),
    )
