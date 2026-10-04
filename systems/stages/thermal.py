"""Stage 09 — Bartz gas-side heat transfer via frozen Physics."""

from __future__ import annotations

import math

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from physics.exceptions import InsufficientDataError, OutOfRangeError
from physics.heat_transfer.bartz import BARTZ, bartz_heat_transfer_coefficient
from physics.quantities import kelvin, metre
from physics.si import (
    UNIT_DYNAMIC_VISCOSITY,
    UNIT_SPECIFIC_HEAT,
    UNIT_THERMAL_CONDUCTIVITY,
)
from systems.contracts.results import (
    CalculationResult,
    ResultStatus,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import failed_result, make_result, stage_guard

__all__ = ("run_thermal_stage",)


@stage_guard("thermal")
def run_thermal_stage(
    design: PropulsionDesign,
    *,
    viscosity_pa_s: float | None = None,
    conductivity_w_m_k: float | None = None,
    cp_j_kg_k: float | None = None,
    wall_temperature_k: float | None = None,
    mach: float | None = None,
    throat_curvature_radius_m: float | None = None,
) -> CalculationResult:
    """Evaluate Bartz HTC at the throat station using OP / nozzle data."""

    stage_id = "thermal"
    op = design.operating_point
    inputs: dict[str, object] = {}
    try:
        saved = design.thermal_design or {}
        values = {
            "viscosity_pa_s": viscosity_pa_s,
            "conductivity_w_m_k": conductivity_w_m_k,
            "cp_j_kg_k": cp_j_kg_k,
            "wall_temperature_k": wall_temperature_k,
        }
        resolved: dict[str, float] = {}
        for key, value in values.items():
            if value is None and key in saved:
                value = float(saved[key])
            if value is None:
                raise InsufficientDataError(
                    f"thermal requires explicit {key}; no engineering default is applied."
                )
            resolved[key] = float(value)
        viscosity_pa_s = resolved["viscosity_pa_s"]
        conductivity_w_m_k = resolved["conductivity_w_m_k"]
        cp_j_kg_k = resolved["cp_j_kg_k"]
        wall_temperature_k = resolved["wall_temperature_k"]
        if op.chamber_pressure is None:
            raise InvalidInputError("thermal requires chamber_pressure.")
        nozzle = design.nozzle_design or {}
        if "throat_area_m2" not in nozzle:
            raise InvalidInputError("thermal requires throat_area_m2.")
        dt = 2.0 * math.sqrt(float(nozzle["throat_area_m2"]) / math.pi)
        if op.characteristic_velocity is None:
            raise InvalidInputError("thermal requires c* (run performance first).")
        local_mach = 1.0 if mach is None else float(mach)
        if op.gamma is None:
            raise InsufficientDataError("thermal requires explicit/derived gamma.")
        gamma = op.gamma
        gamma_assumed = op.gamma_is_assumption
        taw = op.chamber_temperature
        if taw is None:
            raise InvalidInputError(
                "thermal requires chamber_temperature for Taw approximation."
            )

        if throat_curvature_radius_m is None and "throat_curvature_radius_m" in nozzle:
            throat_curvature_radius_m = float(nozzle["throat_curvature_radius_m"])
        if (
            throat_curvature_radius_m is None
            and saved.get("throat_curvature_radius_m") is not None
        ):
            throat_curvature_radius_m = float(saved["throat_curvature_radius_m"])
        curvature = (
            None
            if throat_curvature_radius_m is None
            else metre(throat_curvature_radius_m)
        )
        mu = Quantity(viscosity_pa_s, UNIT_DYNAMIC_VISCOSITY)
        conductivity = Quantity(conductivity_w_m_k, UNIT_THERMAL_CONDUCTIVITY)
        cp = Quantity(cp_j_kg_k, UNIT_SPECIFIC_HEAT)
        inputs = {
            "viscosity": mu.to_canonical_dict(),
            "conductivity": conductivity.to_canonical_dict(),
            "specific_heat": cp.to_canonical_dict(),
            "taw_approximation": "Taw approximated by chamber_temperature; recovery temperature was NOT computed.",
            "adiabatic_wall_temperature": taw.to_canonical_dict(),
            "throat_curvature_radius": None
            if curvature is None
            else curvature.to_canonical_dict(),
            "curvature_correction": "ABSENT" if curvature is None else "APPLIED",
        }

        bartz = bartz_heat_transfer_coefficient(
            metre(dt),
            mu,
            conductivity,
            cp,
            op.chamber_pressure,
            op.characteristic_velocity,
            local_mach,
            float(gamma),
            kelvin(float(wall_temperature_k)),
            taw,
            curvature_radius=curvature,
        )
        design.write_derived_slot(
            "thermal_design",
            {
                "throat_diameter_m": dt,
                "h_w_m2_k": bartz.heat_transfer_coefficient.to_si(),
                "nusselt": bartz.nusselt,
                "reynolds": bartz.reynolds,
                "prandtl": bartz.prandtl,
                "sigma": bartz.sigma,
                "wall_temperature_k": float(wall_temperature_k),
                "viscosity_pa_s": viscosity_pa_s,
                "conductivity_w_m_k": conductivity_w_m_k,
                "cp_j_kg_k": cp_j_kg_k,
                "curvature_factor": bartz.curvature_factor,
                "throat_curvature_radius_m": throat_curvature_radius_m,
            },
        )
        assumptions = [
            "Gas properties (μ, k, Cp) are analysis inputs / assumptions.",
            "Taw approximated by chamber temperature at this stage.",
        ]
        if gamma_assumed:
            assumptions.append(f"gamma = {gamma} treated as assumption.")
        result = make_result(
            calculation_type="thermal.bartz",
            stage_id=stage_id,
            status=ResultStatus.CURRENT,
            model_id=BARTZ.model_id,
            model_version=BARTZ.version,
            inputs={
                **inputs,
                "diameter_m": {"value": dt, "unit": "m"},
                "chamber_pressure": op.chamber_pressure.to_canonical_dict(),
                "cstar": op.characteristic_velocity.to_canonical_dict(),
                "mach": {"value": local_mach, "unit": "1"},
                "gamma": {"value": float(gamma), "unit": "1"},
                "wall_temperature_k": {"value": float(wall_temperature_k), "unit": "K"},
            },
            outputs={
                "h": bartz.heat_transfer_coefficient.to_canonical_dict(),
                "Nu": {"value": bartz.nusselt, "unit": "1"},
                "Re": {"value": bartz.reynolds, "unit": "1"},
                "Pr": {"value": bartz.prandtl, "unit": "1"},
                "sigma": {"value": bartz.sigma, "unit": "1"},
                "curvature_factor": {"value": bartz.curvature_factor, "unit": "1"},
            },
            assumptions=tuple(assumptions),
            warnings=(
                "Validation: NOT_CLAIMED. Bartz correlation — not hot-fire validated here.",
                "Taw APPROXIMATION: chamber temperature used; adiabatic-wall recovery temperature not computed.",
                "Curvature correction absent (radius unavailable)."
                if curvature is None
                else "Curvature correction uses the supplied throat radius.",
            ),
            validity=ValidityInfo(
                status=ValidityState.VALID
                if bartz.validity.value == "VALID"
                else ValidityState.OUT_OF_RANGE,
                valid_range=BARTZ.validity_range,
            ),
            verification=VerificationInfo(
                status="PASS", reference=BARTZ.verification_status
            ),
            source=BARTZ.source,
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        design.workflow.invalidate_from(stage_id)
        design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
        design.workflow.results[stage_id].status = ResultStatus.CURRENT
        return result
    except Exception as exc:  # noqa: BLE001
        result = failed_result(
            calculation_type="thermal.bartz",
            stage_id=stage_id,
            exc=exc,
            design_revision=design.revision,
            model_id=BARTZ.model_id,
            inputs=inputs,
            out_of_range=isinstance(exc, OutOfRangeError),
        )
        design.store_stage_result(stage_id, result)
        return result
