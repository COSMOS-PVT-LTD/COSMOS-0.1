"""Stage 06 — mass flow / nozzle performance from frozen compressible Physics."""

from __future__ import annotations

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.compressible_flow.choked_flow import CHOKED_FLOW, choked_mass_flow
from physics.compressible_flow.nozzle_1d import NOZZLE_1D, station_from_area_ratio
from physics.compressible_flow.thrust_relations import THRUST, ideal_thrust_coefficient, thrust
from physics.exceptions import OutOfRangeError
from physics.quantities import quantity, square_metre
from physics.si import UNIT_MOLAR_MASS

from systems.contracts.results import (
    ResultStatus,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import failed_result, make_result

__all__ = ("run_performance_stage",)

_G0 = 9.80665  # standard gravity [m/s^2] for Isp definition


def run_performance_stage(
    design: PropulsionDesign,
    *,
    throat_area_m2: float | None = None,
    expansion_ratio: float | None = None,
) -> object:
    """
    Compute choked ṁ, exit station, thrust, Cf, Isp using Physics primitives.

    Requires operating-point Pc, Tc, gamma, MW [kg/mol] and geometry At, ε.
    """

    stage_id = "performance"
    op = design.operating_point
    req = design.requirements

    try:
        if op.chamber_pressure is None or op.chamber_temperature is None:
            raise InvalidInputError(
                "performance requires chamber_pressure and chamber_temperature."
            )
        if op.gamma is None or op.molecular_weight is None:
            raise InvalidInputError(
                "performance requires gamma and molecular_weight [kg/mol]."
            )

        at_value = throat_area_m2
        if at_value is None and design.nozzle_design and "throat_area_m2" in design.nozzle_design:
            at_value = float(design.nozzle_design["throat_area_m2"])  # type: ignore[arg-type]
        if at_value is None:
            raise InvalidInputError("performance requires throat_area_m2.")

        eps = expansion_ratio
        if eps is None and req.expansion_ratio is not None:
            eps = float(req.expansion_ratio)
        if eps is None and design.nozzle_design and "expansion_ratio" in design.nozzle_design:
            eps = float(design.nozzle_design["expansion_ratio"])  # type: ignore[arg-type]
        if eps is None:
            raise InvalidInputError("performance requires expansion_ratio.")

        pa = op.ambient_pressure
        if pa is None:
            pa = Quantity(101325.0, SI.get("Pa"))
            ambient_assumption = "ambient_pressure defaulted to 101325 Pa (sea-level)."
        else:
            ambient_assumption = None

        throat = square_metre(float(at_value))
        mw = quantity(float(op.molecular_weight), UNIT_MOLAR_MASS)

        mdot = choked_mass_flow(
            op.chamber_pressure,
            op.chamber_temperature,
            throat,
            float(op.gamma),
            mw,
        )
        exit_station = station_from_area_ratio(
            float(eps),
            op.chamber_pressure,
            op.chamber_temperature,
            float(op.gamma),
            mw,
            branch="supersonic",
        )
        exit_area = square_metre(float(at_value) * float(eps))
        force = thrust(
            mdot,
            exit_station.velocity,
            exit_station.pressure,
            pa,
            exit_area,
        )
        pe_p0 = exit_station.pressure.to_si() / op.chamber_pressure.to_si()
        pa_p0 = pa.to_si() / op.chamber_pressure.to_si()
        cf = ideal_thrust_coefficient(float(op.gamma), pe_p0, pa_p0, float(eps))
        isp = force.to_si() / (mdot.to_si() * _G0) if mdot.to_si() > 0.0 else 0.0
        cstar = op.chamber_pressure.to_si() * float(at_value) / mdot.to_si()
        op.mass_flow = mdot
        op.characteristic_velocity = Quantity(cstar, SI.get("m/s"))

        design.nozzle_design = {
            **(design.nozzle_design or {}),
            "throat_area_m2": float(at_value),
            "expansion_ratio": float(eps),
            "exit_area_m2": float(at_value) * float(eps),
            "exit_mach": exit_station.mach,
        }

        assumptions = [
            "Calorically perfect isentropic choked nozzle (Anderson / Sutton).",
            *([ambient_assumption] if ambient_assumption else []),
        ]
        if op.gamma_is_assumption or op.chamber_temperature_is_assumption:
            assumptions.append("Thermo inputs include explicit analysis assumptions.")

        result = make_result(
            calculation_type="performance.choked_nozzle_thrust",
            stage_id=stage_id,
            status=ResultStatus.CURRENT,
            model_id=f"{CHOKED_FLOW.model_id}+{NOZZLE_1D.model_id}+{THRUST.model_id}",
            model_version=CHOKED_FLOW.version,
            inputs={
                "chamber_pressure": op.chamber_pressure.to_canonical_dict(),
                "chamber_temperature": op.chamber_temperature.to_canonical_dict(),
                "gamma": {"value": op.gamma, "unit": "1"},
                "molar_mass": mw.to_canonical_dict(),
                "throat_area_m2": {"value": float(at_value), "unit": "m2"},
                "expansion_ratio": {"value": float(eps), "unit": "1"},
                "ambient_pressure": pa.to_canonical_dict(),
            },
            outputs={
                "mass_flow": mdot.to_canonical_dict(),
                "exit_mach": {"value": exit_station.mach, "unit": "1"},
                "exit_pressure": exit_station.pressure.to_canonical_dict(),
                "exit_temperature": exit_station.temperature.to_canonical_dict(),
                "exit_velocity": exit_station.velocity.to_canonical_dict(),
                "thrust": force.to_canonical_dict(),
                "thrust_coefficient": {"value": cf, "unit": "1"},
                "specific_impulse": {"value": isp, "unit": "s"},
                "cstar": {"value": cstar, "unit": "m/s"},
            },
            assumptions=tuple(assumptions),
            warnings=(
                "Validation: NOT_CLAIMED. Ideal 1D performance — not hot-fire validated.",
            ),
            validity=ValidityInfo(
                status=ValidityState.VALID,
                checks=("choked_mass_flow", "area_mach_station", "thrust"),
                valid_range=CHOKED_FLOW.validity_range,
            ),
            verification=VerificationInfo(
                status="PASS",
                reference=f"{CHOKED_FLOW.verification_status}; {THRUST.verification_status}",
            ),
            source=f"{CHOKED_FLOW.source}; {NOZZLE_1D.source}; {THRUST.source}",
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        design.workflow.invalidate_from(stage_id)
        design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
        design.workflow.results[stage_id].status = ResultStatus.CURRENT
        return result
    except Exception as exc:  # noqa: BLE001
        result = failed_result(
            calculation_type="performance.choked_nozzle_thrust",
            stage_id=stage_id,
            exc=exc,
            design_revision=design.revision,
            model_id=CHOKED_FLOW.model_id,
            out_of_range=isinstance(exc, OutOfRangeError),
        )
        design.store_stage_result(stage_id, result)
        return result
