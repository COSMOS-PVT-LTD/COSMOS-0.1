"""
COSMOS Rocket Propulsion Platform

Module: physics.compressible_flow.nozzle_1d
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Quasi-1D isentropic nozzle state from area ratio.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.dimension import PRESSURE, TEMPERATURE
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive

from physics.compressible_flow.area_mach import mach_from_area_ratio
from physics.compressible_flow.isentropic import (
    stagnation_density_ratio,
    stagnation_pressure_ratio,
    stagnation_temperature_ratio,
)
from physics.model import ModelIdentity
from physics.quantities import as_si, quantity, require_gamma
from physics.si import SPECIFIC_HEAT
from physics.thermodynamics.ideal_gas import specific_gas_constant, speed_of_sound

__all__ = ("NOZZLE_1D", "NozzleStation", "station_from_area_ratio")

NOZZLE_1D = ModelIdentity(
    model_id="PHYS-004.nozzle.quasi_1d_isentropic",
    model_name="Quasi-1D isentropic nozzle station",
    physical_domain="compressible_flow",
    equations=(
        "A/A* => M (branch)",
        "T = T0 / (1 + ((gamma-1)/2) M^2)",
        "p = p0 / (T0/T)^(gamma/(gamma-1))",
        "V = M * sqrt(gamma R T)",
    ),
    inputs=("A/A* [-]", "p0 [Pa]", "T0 [K]", "gamma [-]", "M [kg/mol]", "branch"),
    outputs=("M [-]", "p [Pa]", "T [K]", "V [m/s]"),
    assumptions=("Isentropic; calorically perfect; quasi-1D.",),
    validity_range="A/A* >= 1; p0 > 0; T0 > 0",
    source="Anderson, Modern Compressible Flow; Sutton & Biblarz.",
    verification_status="analytical_verification: throat M=1; expansion-ratio station",
    limitations=("Shocked nozzles require a normal-shock overlay, not this model alone.",),
)


@dataclass(frozen=True, slots=True)
class NozzleStation:
    """Isentropic nozzle station state."""

    mach: float
    pressure: Quantity
    temperature: Quantity
    density: Quantity
    velocity: Quantity
    area_ratio: float
    branch: str
    identity: ModelIdentity = NOZZLE_1D


def station_from_area_ratio(
    area_ratio: float,
    stagnation_pressure: Quantity,
    stagnation_temperature: Quantity,
    gamma: float,
    molar_mass: Quantity,
    *,
    branch: str = "supersonic",
) -> NozzleStation:
    """Evaluate a quasi-1D isentropic station from A/A*."""

    g = require_gamma(gamma)
    p0 = validate_positive(
        as_si(stagnation_pressure, PRESSURE, "stagnation_pressure"),
        "stagnation_pressure",
    )
    t0 = validate_positive(
        as_si(stagnation_temperature, TEMPERATURE, "stagnation_temperature"),
        "stagnation_temperature",
    )
    mach = mach_from_area_ratio(area_ratio, g, branch=branch)
    t = t0 / stagnation_temperature_ratio(mach, g)
    p = p0 / stagnation_pressure_ratio(mach, g)
    r = as_si(specific_gas_constant(molar_mass), SPECIFIC_HEAT, "R")
    rho0 = p0 / (r * t0)
    rho = rho0 / stagnation_density_ratio(mach, g)
    temperature = quantity(t, SI.get("K"))
    sonic = speed_of_sound(temperature, g, molar_mass)
    velocity = quantity(mach * sonic.to_si(), SI.get("m/s"))
    return NozzleStation(
        mach=mach,
        pressure=quantity(p, SI.get("Pa")),
        temperature=temperature,
        density=quantity(rho, SI.get("kg/m3")),
        velocity=velocity,
        area_ratio=area_ratio,
        branch=branch,
    )
