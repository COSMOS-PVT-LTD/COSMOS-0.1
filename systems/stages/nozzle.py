"""Stage 11 — nozzle geometry / 1D stations (not engine-level thrust)."""

from __future__ import annotations

from systems.contracts.results import (
    CalculationResult,
    ResultStatus,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import failed_result, make_result, stage_guard

__all__ = ("run_nozzle_stage",)


@stage_guard("nozzle")
def run_nozzle_stage(design: PropulsionDesign) -> CalculationResult:
    """
    Record nozzle geometry and isentropic station data already computed by Physics.

    Ownership:
        Nozzle — geometry, area ratio, 1D stations, expansion model identity.
        Performance — mass flow, thrust, engine-level Isp/Cf.
        Contour (MOC) — NOT_IMPLEMENTED.

    Does not introduce a second nozzle solver.
    """

    stage_id = "nozzle"
    performance = design.workflow.current_result("performance")
    geometry = dict(design.nozzle_design or {})
    try:
        if performance is None:
            raise RuntimeError(
                "Nozzle stage requires CURRENT performance (isentropic 1D stations / At, ε)."
            )
        if geometry.get("geometry_status") == "STALE":
            raise RuntimeError(
                "Nozzle geometry is STALE after an upstream change; recalculate Performance."
            )
        outputs = {
            "throat_area_m2": geometry.get("throat_area_m2"),
            "expansion_ratio": geometry.get("expansion_ratio"),
            "exit_area_m2": geometry.get("exit_area_m2"),
            "exit_mach": geometry.get("exit_mach"),
            "exit_pressure": performance.outputs.get("exit_pressure"),
            "exit_temperature": performance.outputs.get("exit_temperature"),
            "contour_model": "NOT_IMPLEMENTED",
            "contour_reason": (
                "Method of characteristics / Rao contour is assigned to Numerics and is "
                "not available in COSMOS 0.1."
            ),
        }
        result = make_result(
            calculation_type="nozzle.isentropic_geometry",
            stage_id=stage_id,
            status=ResultStatus.CURRENT,
            model_id="SYS-11.nozzle.geometry_from_performance",
            model_version="0.1.0",
            inputs={
                "performance_result_id": performance.result_id,
                "cooling_dependency": "BYPASSED_NOT_IMPLEMENTED",
            },
            outputs=outputs,
            assumptions=(
                "Isentropic 1D station data reused from the Performance stage Physics call.",
                "No second area-Mach solver is executed here.",
            ),
            warnings=(
                "MOC / wall-contour generation is NOT_IMPLEMENTED.",
                "Validation: NOT_CLAIMED.",
            ),
            validity=ValidityInfo(status=ValidityState.VALID),
            verification=VerificationInfo(
                status="SOFTWARE_IDENTITY",
                reference="Nozzle geometry envelope from Systems; Physics identity remains on Performance.",
            ),
            source="systems.stages.nozzle",
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
        design.workflow.graph.get(stage_id).implementation_status = (
            design.workflow.graph.get(stage_id).implementation_status
        )
        return result
    except Exception as exc:  # noqa: BLE001
        result = failed_result(
            calculation_type="nozzle.isentropic_geometry",
            stage_id=stage_id,
            exc=exc,
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        return result
