"""Stage 09 — Bartz gas-side heat transfer via frozen Physics."""

from __future__ import annotations

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.exceptions import OutOfRangeError
from physics.heat_transfer.bartz import BARTZ, bartz_heat_transfer_coefficient
from physics.quantities import kelvin, metre
from physics.si import UNIT_DYNAMIC_VISCOSITY, UNIT_SPECIFIC_HEAT, UNIT_THERMAL_CONDUCTIVITY

from systems.contracts.results import ResultStatus, ValidityInfo, ValidityState, VerificationInfo
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import failed_result, make_result

__all__ = ("run_thermal_stage",)


def run_thermal_stage(
    design: PropulsionDesign,
    *,
    viscosity_pa_s: float = 8.0e-5,
    conductivity_w_m_k: float = 0.3,
    cp_j_kg_k: float = 2500.0,
    wall_temperature_k: float = 800.0,
    mach: float | None = None,
) -> object:
    """Evaluate Bartz HTC at the throat station using OP / nozzle data."""

    stage_id = "thermal"
    op = design.operating_point
    try:
        if op.chamber_pressure is None:
            raise InvalidInputError("thermal requires chamber_pressure.")
        nozzle = design.nozzle_design or {}
        if "throat_area_m2" not in nozzle:
            raise InvalidInputError("thermal requires throat_area_m2.")
        import math

        dt = 2.0 * math.sqrt(float(nozzle["throat_area_m2"]) / math.pi)
        if op.characteristic_velocity is None:
            raise InvalidInputError("thermal requires c* (run performance first).")
        local_mach = 1.0 if mach is None else float(mach)
        gamma = op.gamma if op.gamma is not None else 1.2
        gamma_assumed = op.gamma is None or op.gamma_is_assumption
        taw = op.chamber_temperature
        if taw is None:
            raise InvalidInputError("thermal requires chamber_temperature for Taw approximation.")

        bartz = bartz_heat_transfer_coefficient(
            metre(dt),
            Quantity(float(viscosity_pa_s), UNIT_DYNAMIC_VISCOSITY),
            Quantity(float(conductivity_w_m_k), UNIT_THERMAL_CONDUCTIVITY),
            Quantity(float(cp_j_kg_k), UNIT_SPECIFIC_HEAT),
            op.chamber_pressure,
            op.characteristic_velocity,
            local_mach,
            float(gamma),
            kelvin(float(wall_temperature_k)),
            taw,
        )
        design.thermal_design = {
            "throat_diameter_m": dt,
            "h_w_m2_k": bartz.heat_transfer_coefficient.to_si(),
            "nusselt": bartz.nusselt,
            "reynolds": bartz.reynolds,
            "prandtl": bartz.prandtl,
            "sigma": bartz.sigma,
            "wall_temperature_k": float(wall_temperature_k),
        }
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
            },
            assumptions=tuple(assumptions),
            warnings=("Validation: NOT_CLAIMED. Bartz correlation — not hot-fire validated here.",),
            validity=ValidityInfo(
                status=ValidityState.VALID
                if bartz.validity.value == "VALID"
                else ValidityState.OUT_OF_RANGE,
                valid_range=BARTZ.validity_range,
            ),
            verification=VerificationInfo(status="PASS", reference=BARTZ.verification_status),
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
            out_of_range=isinstance(exc, OutOfRangeError),
        )
        design.store_stage_result(stage_id, result)
        return result
