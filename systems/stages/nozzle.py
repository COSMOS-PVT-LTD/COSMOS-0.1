"""Stage 11 — nozzle geometry / 1D stations (not engine-level thrust)."""

from __future__ import annotations

import math
from dataclasses import asdict

from physics.compressible_flow.bell_nozzle import (
    BELL_CONTOUR,
    bell_contour,
    flow_stations,
)
from physics.exceptions import InsufficientDataError
from physics.quantities import metre
from systems.contracts.results import (
    CalculationResult,
    ResultStatus,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import failed_result, make_result, stage_guard
from systems.stages.subsystems import require_fields

__all__ = ("run_nozzle_stage",)


@stage_guard("nozzle")
def run_nozzle_stage(
    design: PropulsionDesign, *, require_contour: bool = False
) -> CalculationResult:
    """
    Record nozzle geometry and isentropic station data already computed by Physics.

    Ownership:
        Nozzle — geometry, area ratio, 1D stations, expansion model identity.
        Performance — mass flow, thrust, engine-level Isp/Cf.
        Tangent bell contour — explicit geometry; optimized MOC remains unavailable.

    Reuses the existing Physics area-Mach solver for the generated contour.
    """

    stage_id = "nozzle"
    performance = design.workflow.current_result("performance")
    geometry = dict(design.nozzle_design or {})
    try:
        if performance is None:
            raise RuntimeError(
                "Nozzle stage requires CURRENT performance (isentropic 1D stations / At, ε)."
            )
        cfg = design.subsystem_inputs.get("nozzle", {})
        if require_contour and not cfg:
            raise InsufficientDataError(
                "Enter explicit nozzle contour inputs before generation."
            )
        if cfg:
            result = _contour_result(design, performance, cfg)
            design.write_derived_slot("nozzle_design", result.outputs)
            design.store_stage_result(stage_id, result)
            return result
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
            "contour_model": "NOT_CALCULATED",
            "contour_reason": (
                "Enter explicit bell-contour geometry inputs to generate a wall contour. "
                "Optimized Rao / MOC remains unsupported."
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
                "cooling_dependency": "GEOMETRY_INDEPENDENT_OF_COOLING",
            },
            outputs=outputs,
            assumptions=(
                "Isentropic 1D station data reused from the Performance stage Physics call.",
                "No second area-Mach solver is executed here.",
            ),
            warnings=(
                "Bell wall contour NOT_CALCULATED; only 1D area geometry is present.",
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
        design.workflow.graph.get(
            stage_id
        ).implementation_status = design.workflow.graph.get(
            stage_id
        ).implementation_status
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


def _contour_result(
    design: PropulsionDesign, performance: CalculationResult, cfg: dict
) -> CalculationResult:
    require_fields(
        cfg,
        {
            "length_fraction",
            "start_angle_deg",
            "exit_angle_deg",
            "blend_radius_ratio",
            "point_count",
        },
    )
    op = design.operating_point
    if (
        op.gamma is None
        or op.chamber_temperature is None
        or op.chamber_pressure is None
    ):
        raise InsufficientDataError(
            "Contour stations require CURRENT gamma, chamber temperature and pressure."
        )
    # Performance owns At and epsilon; a stale contour slot is never the authority.
    at = float(performance.inputs["throat_area_m2"]["value"])
    eps = float(performance.inputs["expansion_ratio"]["value"])
    points = bell_contour(
        metre(math.sqrt(at / math.pi)),
        eps,
        cfg["length_fraction"],
        cfg["start_angle_deg"],
        cfg["exit_angle_deg"],
        cfg["blend_radius_ratio"],
        cfg["point_count"],
    )
    rows = [
        asdict(row)
        for row in flow_stations(
            points, op.chamber_pressure, op.chamber_temperature, op.gamma
        )
    ]
    return make_result(
        calculation_type="nozzle.tangent_bell",
        stage_id="nozzle",
        status=ResultStatus.CURRENT,
        model_id=BELL_CONTOUR.model_id,
        model_version=BELL_CONTOUR.version,
        inputs={
            **cfg,
            "performance_result_id": performance.result_id,
            "throat_area_m2": at,
            "expansion_ratio": eps,
            "gamma": op.gamma,
            "chamber_pressure": op.chamber_pressure.to_canonical_dict(),
            "chamber_temperature": op.chamber_temperature.to_canonical_dict(),
        },
        outputs={
            "throat_area_m2": at,
            "expansion_ratio": eps,
            "exit_area_m2": at * eps,
            "exit_mach": rows[-1]["mach"],
            "length_m": points[-1].x_m,
            "throat_curvature_radius_m": cfg["blend_radius_ratio"] * points[0].radius_m,
            "contour_model": BELL_CONTOUR.model_id,
            "stations": rows,
        },
        assumptions=BELL_CONTOUR.assumptions
        + (
            "Contour station properties use constant chamber gamma/Tc/MW, including when these are sourced from CEA; they are NOT CEA equilibrium nozzle stations. Performance uses CEA exit states in CEA mode.",
        ),
        warnings=BELL_CONTOUR.limitations,
        validity=ValidityInfo(
            status=ValidityState.UNKNOWN, valid_range=BELL_CONTOUR.validity_range
        ),
        verification=VerificationInfo(
            status="SOFTWARE_VERIFIED", reference=BELL_CONTOUR.verification_status
        ),
        source=BELL_CONTOUR.source,
        design_revision=design.revision,
    )
