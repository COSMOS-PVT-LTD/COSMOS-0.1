"""Stage 16 — design review provenance package."""

from __future__ import annotations

from core.version import COSMOS_VERSION
from systems.contracts.results import (
    CalculationResult,
    ResultStatus,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import make_result, stage_guard
from systems.workflow.graph import StageImplementationStatus
from systems.workflow.readiness import readiness_payload

__all__ = ("run_design_review_stage",)

# Capabilities that prevent a READY verdict until implemented or explicitly waived.
_BLOCKING_UNIMPLEMENTED = ("injector", "cooling", "cycle")


@stage_guard("design_review")
def run_design_review_stage(design: PropulsionDesign) -> CalculationResult:
    """
    Assemble a design-review package from workflow artifacts.

    Does not claim flight certification or experimental validation.
    Verdict is READY / INCOMPLETE / BLOCKED — never READY while mandatory
    capabilities remain NOT_IMPLEMENTED, STALE, or FAILED.
    """

    stage_id = "design_review"
    consistency = design.workflow.current_result("consistency")
    summary = design.workflow.current_result("performance_summary")

    stage_table: list[dict[str, object]] = []
    incomplete_reasons: list[str] = []
    blocked_reasons: list[str] = []

    for sid, node in sorted(design.workflow.graph.nodes.items()):
        stored = design.workflow.results.get(sid)
        current = design.workflow.current_result(sid)
        status_value = (
            current.status.value
            if current is not None
            else (stored.status.value if stored is not None else node.status.value)
        )
        stage_table.append(
            {
                "stage_id": sid,
                "name": node.name,
                "implementation_status": node.implementation_status.value,
                "status": status_value,
                "has_current": current is not None,
                "model_id": None if stored is None else stored.model_id,
                "validation": (
                    None if stored is None else stored.validation.to_canonical_dict()
                ),
                "verification": (
                    None if stored is None else stored.verification.to_canonical_dict()
                ),
            }
        )
        if sid == stage_id:
            # The review being regenerated is not an upstream dependency.
            continue
        if (node.implementation_status is StageImplementationStatus.NOT_IMPLEMENTED
                and sid in _BLOCKING_UNIMPLEMENTED):
            incomplete_reasons.append(
                f"{sid} is NOT_IMPLEMENTED — {node.name} has no validated Physics model."
            )
        stored_status = None if stored is None else stored.status
        if stored_status in {ResultStatus.FAILED, ResultStatus.OUT_OF_RANGE}:
            blocked_reasons.append(f"{sid} result is {stored_status.value}.")
        if stored_status is ResultStatus.STALE:
            incomplete_reasons.append(f"{sid} result is STALE and must be recalculated.")
        if (stored_status is ResultStatus.NOT_CALCULATED or (
            stored is None and node.status is not ResultStatus.CURRENT
        )) and sid not in {"design_review"}:
            incomplete_reasons.append(f"{sid} is NOT_CALCULATED.")
        if stored_status is ResultStatus.NOT_IMPLEMENTED:
            incomplete_reasons.append(f"{sid} result is NOT_IMPLEMENTED.")

    consistent = bool(
        consistency is not None
        and consistency.status is ResultStatus.CURRENT
        and consistency.outputs.get("consistent") is True
    )

    if not consistent:
        blocked_reasons.append("Consistency stage is not CURRENT/consistent.")
    if summary is None:
        blocked_reasons.append("Performance summary missing.")

    if blocked_reasons:
        verdict = "BLOCKED"
    elif incomplete_reasons:
        verdict = "INCOMPLETE"
    else:
        verdict = "READY"

    package = {
        "design_id": design.design_id,
        "name": design.name,
        "revision": design.revision,
        "software_version": design.software_version or COSMOS_VERSION,
        "engineer": design.engineer,
        "requirements": design.requirements.to_canonical_dict(),
        "propellant_configuration": design.propellant_configuration.to_canonical_dict(),
        "cycle_configuration": design.cycle_configuration.to_canonical_dict(),
        "operating_point": design.operating_point.to_canonical_dict(),
        "subsystem_slots": {
            "injector_design": design.injector_design,
            "chamber_design": design.chamber_design,
            "thermal_design": design.thermal_design,
            "cooling_design": design.cooling_design,
            "nozzle_design": design.nozzle_design,
            "structural_design": design.structural_design,
            "material_selection": design.material_selection,
        },
        "performance_summary": None
        if summary is None
        else summary.outputs.get("consolidated"),
        "consistency": None if consistency is None else consistency.outputs,
        "stages": stage_table,
        "change_log": [event.to_canonical_dict() for event in design.change_log[-20:]],
        "review_verdict": verdict,
        "incomplete_reasons": incomplete_reasons,
        "blocked_reasons": blocked_reasons,
        "certification_statement": (
            "NOT flight-certified. Validation status remains NOT_CLAIMED. "
            "This package is a computational design-review artifact for COSMOS 0.1."
        ),
    }

    warnings = tuple(blocked_reasons + incomplete_reasons)
    assembled = summary is not None
    status = ResultStatus.CURRENT if assembled else ResultStatus.FAILED

    result = make_result(
        calculation_type="workflow.design_review",
        stage_id=stage_id,
        status=status,
        model_id="systems.design_review",
        model_version="0.2.0",
        inputs={
            "consistency_result_id": None if consistency is None else consistency.result_id,
            "summary_result_id": None if summary is None else summary.result_id,
        },
        outputs={
            "package": package,
            "review_verdict": verdict,
            "review_ready": verdict == "READY",
            "incomplete_reasons": incomplete_reasons,
            "blocked_reasons": blocked_reasons,
            "readiness": readiness_payload(design.workflow),
        },
        warnings=warnings,
        validity=ValidityInfo(
            status=ValidityState.VALID if verdict == "READY" else ValidityState.UNKNOWN,
            checks=("consistency_current", "summary_current", "mandatory_capabilities"),
            violations=warnings,
        ),
        verification=VerificationInfo(
            status="PASS" if assembled else "FAIL",
            reference="Design-review assembly from Systems workflow artifacts.",
        ),
        source="systems.stages.design_review",
        design_revision=design.revision,
    )
    design.store_stage_result(stage_id, result)
    return result
