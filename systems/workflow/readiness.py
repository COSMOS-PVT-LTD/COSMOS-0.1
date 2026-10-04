"""Engineering readiness is independent of calculation freshness and validation."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from systems.contracts.results import ResultStatus, ValidityState
from systems.workflow.graph import DependencyRequirement, StageImplementationStatus

if TYPE_CHECKING:
    from systems.workflow.state import WorkflowState


class EngineeringReadiness(str, Enum):
    INCOMPLETE = "INCOMPLETE"
    PRELIMINARY = "PRELIMINARY"
    VALIDATION_REQUIRED = "VALIDATION_REQUIRED"


def dependency_assessment(
    state: WorkflowState, stage_id: str
) -> list[dict[str, str | bool]]:
    rows: list[dict[str, str | bool]] = []
    for edge in state.graph.get(stage_id).dependencies:
        result = state.results.get(edge.stage_id)
        status = ResultStatus.NOT_CALCULATED if result is None else result.status
        if result is None and edge.stage_id == "design_project":
            status = state.graph.get(edge.stage_id).status
        if result is not None and result.validity.status is ValidityState.OUT_OF_RANGE:
            status = ResultStatus.OUT_OF_RANGE
        rows.append(
            {
                **edge.to_canonical_dict(),
                "status": status.value,
                "satisfied": status is ResultStatus.CURRENT,
            }
        )
    return rows


def readiness_payload(state: WorkflowState) -> dict[str, object]:
    missing = []
    dependency_gaps = []
    for stage_id, node in state.graph.nodes.items():
        result = state.current_result(stage_id)
        identity_exists = (
            stage_id == "design_project" and node.status is ResultStatus.CURRENT
        )
        if (
            node.implementation_status is StageImplementationStatus.NOT_IMPLEMENTED
            or (result is None and not identity_exists)
            or (
                result is not None
                and result.validity.status is ValidityState.OUT_OF_RANGE
            )
        ):
            missing.append(stage_id)
        for dep in dependency_assessment(state, stage_id):
            if dep["satisfied"] is False:
                dependency_gaps.append({"downstream": stage_id, **dep})
    blocked = any(
        row["requirement"] == DependencyRequirement.REQUIRED.value
        and state.current_result(str(row["downstream"])) is not None
        for row in dependency_gaps
    )
    complete = not missing and not blocked
    readiness = EngineeringReadiness.INCOMPLETE
    if state.current_result("performance") is not None and not blocked:
        readiness = EngineeringReadiness.PRELIMINARY
    if complete:
        readiness = EngineeringReadiness.VALIDATION_REQUIRED
    # Reuse CalculationResult.validation; software tests cannot upgrade a
    # design's validation level. Detailed per-stage states remain available.
    validation = {
        key: result.validation.status for key, result in state.results.items()
    }
    levels = set(validation.values())
    level = next(iter(levels)) if len(levels) == 1 else "NOT_CLAIMED"
    return {
        "workflow_complete": complete,
        "engineering_readiness": readiness.value,
        "validation_level": level,
        "stage_validation": validation,
        "missing_stages": missing,
        "dependency_gaps": dependency_gaps,
    }
