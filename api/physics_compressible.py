"""
Application adapter: compressible-flow Physics for the COSMOS GUI/API boundary.

GUI and presentation code must call this module (or HTTP routes that wrap it).
They must not import Physics equations or duplicate Core unit conversion.
"""

from __future__ import annotations

from typing import Any

from core.exceptions import (
    CosmosError,
    InvalidInputError,
    SolverConvergenceError,
    UnitError,
)
from core.version import COSMOS_VERSION
from physics.compressible_flow.area_mach import AREA_MACH, area_ratio, mach_from_area_ratio
from physics.compressible_flow.isentropic import (
    ISENTROPIC,
    stagnation_density_ratio,
    stagnation_pressure_ratio,
    stagnation_temperature_ratio,
)
from physics.exceptions import OutOfRangeError, PhysicsError
from physics.model import ModelIdentity, PHYSICS_SCHEMA_VERSION

__all__ = (
    "evaluate_area_mach",
    "evaluate_bartz_htc",
    "evaluate_isentropic_stagnation",
    "evaluate_thin_wall_stress",
    "map_engineering_error",
)


def _model_payload(identity: ModelIdentity) -> dict[str, Any]:
    return {
        "model_id": identity.model_id,
        "model_name": identity.model_name,
        "version": identity.version,
        "physical_domain": identity.physical_domain,
        "equations": list(identity.equations),
        "assumptions": list(identity.assumptions),
        "validity_range": identity.validity_range,
        "source": identity.source,
        "verification_status": identity.verification_status,
        "validation_status": "NOT_CLAIMED",
        "limitations": list(identity.limitations),
        "numerical_method_dependency": identity.numerical_method_dependency,
        "software_version": COSMOS_VERSION,
        "physics_schema_version": PHYSICS_SCHEMA_VERSION,
    }


def map_engineering_error(exc: BaseException) -> tuple[int, dict[str, object]]:
    """Map typed engineering exceptions to HTTP-ish status + payload."""

    if isinstance(exc, (InvalidInputError, UnitError, ValueError, TypeError, KeyError)):
        code = "InvalidInputError" if not isinstance(exc, UnitError) else "UnitError"
        if isinstance(exc, KeyError):
            message = f"Missing required field: {exc.args[0]!r}."
        else:
            message = str(exc)
        status = 400
    elif isinstance(exc, OutOfRangeError):
        code = "OutOfRangeError"
        message = str(exc)
        status = 422
    elif isinstance(exc, SolverConvergenceError):
        code = "SolverConvergenceError"
        message = str(exc)
        status = 422
    elif isinstance(exc, (PhysicsError, CosmosError)):
        code = type(exc).__name__
        message = str(exc)
        status = 400
    else:
        code = "InternalError"
        message = str(exc)
        status = 500
    return status, {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "action": "Correct the input or select a valid model range. Inputs are not silently repaired.",
        },
    }


def evaluate_bartz_htc(payload: dict[str, object]) -> dict[str, object]:
    """Evaluate Bartz gas-side heat-transfer coefficient from SI inputs."""

    from core.quantity import Quantity
    from core.unit import SI
    from physics.heat_transfer.bartz import BARTZ, bartz_heat_transfer_coefficient
    from physics.quantities import kelvin, metre, pascal
    from physics.si import (
        UNIT_DYNAMIC_VISCOSITY,
        UNIT_SPECIFIC_HEAT,
        UNIT_THERMAL_CONDUCTIVITY,
    )

    diameter = float(payload["diameter_m"])
    viscosity = float(payload["viscosity_pa_s"])
    conductivity = float(payload["conductivity_w_m_k"])
    specific_heat = float(payload["cp_j_kg_k"])
    chamber_pressure = float(payload["chamber_pressure_pa"])
    cstar = float(payload["cstar_m_s"])
    mach = float(payload["mach"])
    gamma = float(payload["gamma"])
    wall_t = float(payload["wall_temperature_k"])
    aw_t = float(payload["adiabatic_wall_temperature_k"])
    curvature = payload.get("curvature_radius_m")
    curvature_q = None if curvature is None else metre(float(curvature))

    result = bartz_heat_transfer_coefficient(
        metre(diameter),
        Quantity(viscosity, UNIT_DYNAMIC_VISCOSITY),
        Quantity(conductivity, UNIT_THERMAL_CONDUCTIVITY),
        Quantity(specific_heat, UNIT_SPECIFIC_HEAT),
        pascal(chamber_pressure),
        Quantity(cstar, SI.get("m/s")),
        mach,
        gamma,
        kelvin(wall_t),
        kelvin(aw_t),
        curvature_radius=curvature_q,
    )
    return {
        "ok": True,
        "operation": "bartz_htc",
        "model": _model_payload(BARTZ),
        "inputs": {
            "diameter": {"value": diameter, "unit": "m"},
            "viscosity": {"value": viscosity, "unit": "Pa s"},
            "conductivity": {"value": conductivity, "unit": "W/(m K)"},
            "Cp": {"value": specific_heat, "unit": "J/(kg K)"},
            "chamber_pressure": {"value": chamber_pressure, "unit": "Pa"},
            "cstar": {"value": cstar, "unit": "m/s"},
            "mach": {"value": mach, "unit": "1"},
            "gamma": {"value": gamma, "unit": "1"},
            "wall_temperature": {"value": wall_t, "unit": "K"},
            "adiabatic_wall_temperature": {"value": aw_t, "unit": "K"},
            "curvature_radius": {
                "value": None if curvature is None else float(curvature),
                "unit": "m",
            },
        },
        "outputs": {
            "h": {"value": result.heat_transfer_coefficient.to_si(), "unit": "W/(m2 K)"},
            "Nu": {"value": result.nusselt, "unit": "1"},
            "Re": {"value": result.reynolds, "unit": "1"},
            "Pr": {"value": result.prandtl, "unit": "1"},
            "sigma": {"value": result.sigma, "unit": "1"},
            "curvature_factor": {"value": result.curvature_factor, "unit": "1"},
        },
        "warnings": [
            f"Validity: {result.validity.value}",
            "Validation: NOT_CLAIMED (engineering correlation, not hot-fire validated here).",
        ],
        "verification": {"status": BARTZ.verification_status, "result": "PASS"},
        "validation": {"status": "NOT_CLAIMED"},
    }


def evaluate_thin_wall_stress(payload: dict[str, object]) -> dict[str, object]:
    """Thin-wall cylinder hoop/longitudinal stress from Physics."""

    from physics.materials.catalog import STAINLESS_304
    from physics.materials.elastic_properties import yield_strength
    from physics.quantities import kelvin, metre, pascal
    from physics.solid_mechanics.pressure_vessels import cylinder
    from physics.model import ModelIdentity

    pressure = float(payload["pressure_pa"])
    radius = float(payload["radius_m"])
    thickness = float(payload["thickness_m"])
    temperature = float(payload.get("temperature_k") or 300.0)
    wall = cylinder(pascal(pressure), metre(radius), metre(thickness))
    sy = yield_strength(STAINLESS_304, kelvin(temperature)).require_valid()
    identity = ModelIdentity(
        model_id="PHYS-007.pressure_vessel.thin_wall",
        model_name="Thin-wall cylindrical pressure stress",
        physical_domain="solid_mechanics",
        equations=("sigma_h = p r / t", "sigma_l = p r / (2 t)"),
        inputs=("p [Pa]", "r [m]", "t [m]"),
        outputs=("sigma_h [Pa]", "sigma_l [Pa]"),
        assumptions=("Thin-wall membrane theory; not an ASME design code.",),
        validity_range="Typically r/t >= 10; room-temperature material window for yield lookup.",
        source="Roark / Shigley physics relations (not certified allowables).",
        verification_status="analytical_verification: hoop = pr/t identity",
        limitations=("Not MMPDS; not PED/ASME design workflow.",),
    )
    return {
        "ok": True,
        "operation": "thin_wall_stress",
        "model": _model_payload(identity),
        "inputs": {
            "pressure": {"value": pressure, "unit": "Pa"},
            "radius": {"value": radius, "unit": "m"},
            "thickness": {"value": thickness, "unit": "m"},
            "temperature": {"value": temperature, "unit": "K"},
            "material": {"value": "STAINLESS_304", "unit": "1"},
        },
        "outputs": {
            "hoop_stress": {"value": wall.hoop.to_si(), "unit": "Pa"},
            "longitudinal_stress": {"value": wall.longitudinal.to_si(), "unit": "Pa"},
            "yield_strength": {"value": sy.to_si(), "unit": "Pa"},
            "r_over_t": {"value": radius / thickness, "unit": "1"},
            "hoop_over_yield": {"value": wall.hoop.to_si() / sy.to_si(), "unit": "1"},
        },
        "warnings": [
            "Material yield is room-temperature handbook typical, not a certified allowable.",
        ],
        "verification": {"status": identity.verification_status, "result": "PASS"},
        "validation": {"status": "NOT_CLAIMED"},
    }


def evaluate_isentropic_stagnation(mach: float, gamma: float) -> dict[str, object]:
    """
    Evaluate isentropic stagnation ratios.

    Inputs are dimensionless Mach and gamma. Physics validates via require_mach /
    require_gamma. No GUI-side equation evaluation.
    """

    t_ratio = stagnation_temperature_ratio(mach, gamma)
    p_ratio = stagnation_pressure_ratio(mach, gamma)
    rho_ratio = stagnation_density_ratio(mach, gamma)
    return {
        "ok": True,
        "operation": "isentropic_stagnation",
        "model": _model_payload(ISENTROPIC),
        "inputs": {
            "mach": {"value": float(mach), "unit": "1"},
            "gamma": {"value": float(gamma), "unit": "1"},
        },
        "outputs": {
            "T0_over_T": {"value": t_ratio, "unit": "1"},
            "p0_over_p": {"value": p_ratio, "unit": "1"},
            "rho0_over_rho": {"value": rho_ratio, "unit": "1"},
        },
        "warnings": [],
        "verification": {
            "status": ISENTROPIC.verification_status,
            "result": "PASS",
        },
        "validation": {"status": "NOT_CLAIMED"},
    }


def evaluate_area_mach(
    *,
    mode: str,
    gamma: float,
    mach: float | None = None,
    area_ratio_value: float | None = None,
    branch: str = "supersonic",
) -> dict[str, object]:
    """
    Forward A/A*(M) or inverse M(A/A*) via Physics.

    mode:
        ``forward`` requires ``mach``; ``inverse`` requires ``area_ratio_value``.
    """

    mode_key = str(mode).strip().lower()
    if mode_key == "forward":
        if mach is None:
            raise InvalidInputError("forward area-Mach requires mach.")
        ratio = area_ratio(float(mach), gamma)
        return {
            "ok": True,
            "operation": "area_mach_forward",
            "model": _model_payload(AREA_MACH),
            "inputs": {
                "mach": {"value": float(mach), "unit": "1"},
                "gamma": {"value": float(gamma), "unit": "1"},
            },
            "outputs": {
                "A_over_Astar": {"value": ratio, "unit": "1"},
            },
            "warnings": [],
            "verification": {
                "status": AREA_MACH.verification_status,
                "result": "PASS",
            },
            "validation": {"status": "NOT_CLAIMED"},
        }

    if mode_key == "inverse":
        if area_ratio_value is None:
            raise InvalidInputError("inverse area-Mach requires area_ratio.")
        recovered = mach_from_area_ratio(
            float(area_ratio_value),
            gamma,
            branch=str(branch),
        )
        return {
            "ok": True,
            "operation": "area_mach_inverse",
            "model": _model_payload(AREA_MACH),
            "inputs": {
                "A_over_Astar": {"value": float(area_ratio_value), "unit": "1"},
                "gamma": {"value": float(gamma), "unit": "1"},
                "branch": {"value": str(branch), "unit": "1"},
            },
            "outputs": {
                "mach": {"value": recovered, "unit": "1"},
            },
            "warnings": [
                "Inverse uses temporary PHYS-004 numerics_port bisection (PATH A waiver).",
            ],
            "verification": {
                "status": AREA_MACH.verification_status,
                "result": "PASS",
            },
            "validation": {"status": "NOT_CLAIMED"},
        }

    raise InvalidInputError("mode must be 'forward' or 'inverse'.")
