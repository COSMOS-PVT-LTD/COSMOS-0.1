"""Stage 16 — design review provenance package."""

from __future__ import annotations

from core.version import COSMOS_VERSION

from systems.contracts.results import (
    ResultStatus,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import make_result

__all__ = ("run_design_review_stage",)


def run_design_review_stage(design: PropulsionDesign) -> object:
    """
    Assemble a design-review package from workflow artifacts.

    Does not claim flight certification or experimental validation.
    """

    stage_id = "design_review"
    consistency = design.workflow.current_result("consistency")
    summary = design.workflow.current_result("performance_summary")

    stage_table: list[dict[str, object]] = []
    for sid, node in sorted(design.workflow.graph.nodes.items()):
        stored = design.workflow.results.get(sid)
        current = design.workflow.current_result(sid)
        stage_table.append(
            {
                "stage_id": sid,
                "name": node.name,
                "implementation_status": node.implementation_status.value,
                "status": (
                    current.status.value
                    if current is not None
                    else (stored.status.value if stored is not None else node.status.value)
                ),
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

    consistent = bool(
        consistency is not None
        and consistency.status is ResultStatus.CURRENT
        and consistency.outputs.get("consistent") is True
    )

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
        "certification_statement": (
            "NOT flight-certified. Validation status remains NOT_CLAIMED. "
            "This package is a computational design-review artifact for COSMOS 0.1."
        ),
    }

    warnings: list[str] = []
    if not consistent:
        warnings.append("Consistency stage is not CURRENT/consistent — review incomplete.")
    if summary is None:
        warnings.append("Performance summary missing — review incomplete.")

    status = ResultStatus.CURRENT if consistent and summary is not None else ResultStatus.FAILED

    result = make_result(
        calculation_type="workflow.design_review",
        stage_id=stage_id,
        status=status,
        model_id="systems.design_review",
        model_version="0.1",
        inputs={
            "consistency_result_id": None if consistency is None else consistency.result_id,
            "summary_result_id": None if summary is None else summary.result_id,
        },
        outputs={"package": package, "review_ready": status is ResultStatus.CURRENT},
        warnings=tuple(warnings),
        validity=ValidityInfo(
            status=ValidityState.VALID if status is ResultStatus.CURRENT else ValidityState.UNKNOWN,
            checks=("consistency_current", "summary_current"),
            violations=tuple(warnings),
        ),
        verification=VerificationInfo(
            status="PASS" if status is ResultStatus.CURRENT else "FAIL",
            reference="Design-review assembly from Systems workflow artifacts.",
        ),
        source="systems.stages.design_review",
        design_revision=design.revision,
    )
    design.store_stage_result(stage_id, result)
    return result
