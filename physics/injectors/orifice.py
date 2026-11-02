"""Incompressible liquid orifice sizing with explicit discharge coefficient."""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.dimension import DENSITY, MASS_FLOW_RATE, PRESSURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive
from physics.model import ModelIdentity
from physics.quantities import as_si
from physics.si import DYNAMIC_VISCOSITY

LIQUID_ORIFICE = ModelIdentity(
    model_id="PHYS-INJ.liquid_orifice",
    model_name="Liquid injector orifice hydraulic sizing",
    physical_domain="injectors",
    equations=(
        "mdot = Cd A sqrt(2 rho delta_p)",
        "d = sqrt(4 A / (pi N))",
        "u = mdot / (rho A)",
        "Re = rho u d / mu",
    ),
    inputs=(
        "mdot [kg/s]",
        "rho [kg/m3]",
        "delta_p [Pa]",
        "mu [Pa s]",
        "Cd [-]",
        "N [-]",
    ),
    outputs=("total area [m2]", "hole diameter [m]", "velocity [m/s]", "Re [-]"),
    assumptions=(
        "Single-phase incompressible liquid; identical circular holes.",
        "Cd supplied for the actual geometry and operating state, not inferred.",
    ),
    validity_range="mdot,rho,delta_p,mu > 0; 0 < Cd <= 1; integer 1 <= N <= 100000",
    source="NASA SP-8089, Liquid Rocket Engine Injectors, hydraulic design; https://ntrs.nasa.gov/citations/19760023196",
    verification_status="analytical round-trip and scaling tests",
    limitations=(
        "No spray/atomization, element layout, mixing, cavitation or combustion stability prediction.",
        "Does not size gas, flashing or two-phase injectors.",
    ),
)


def hole_count(value: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 100000
    ):
        raise InvalidInputError("hole_count must be an integer from 1 to 100000.")
    return value


def bipropellant_mass_split(
    mass_flow: Quantity, mixture_ratio: float
) -> tuple[Quantity, Quantity]:
    """Return oxidizer, fuel core flow (no film or cycle diversion assumed)."""
    total = validate_positive(
        as_si(mass_flow, MASS_FLOW_RATE, "mass_flow"), "mass_flow"
    )
    ratio = validate_positive(mixture_ratio, "mixture_ratio")
    fuel = total / (1 + ratio)
    return Quantity(total - fuel, SI.get("kg/s")), Quantity(fuel, SI.get("kg/s"))


@dataclass(frozen=True, slots=True)
class OrificeSizing:
    mass_flow_kg_s: float
    total_area_m2: float
    area_per_hole_m2: float
    diameter_m: float
    velocity_m_s: float
    reynolds: float
    momentum_rate_n: float
    hole_count: int


def liquid_orifice(
    mass_flow: Quantity,
    density: Quantity,
    pressure_drop: Quantity,
    viscosity: Quantity,
    discharge_coefficient: float,
    count: int,
) -> OrificeSizing:
    """Size geometric area; velocity includes Cd (not the ideal jet velocity)."""
    mdot = validate_positive(as_si(mass_flow, MASS_FLOW_RATE, "mass_flow"), "mass_flow")
    rho = validate_positive(as_si(density, DENSITY, "density"), "density")
    dp = validate_positive(
        as_si(pressure_drop, PRESSURE, "pressure_drop"), "pressure_drop"
    )
    mu = validate_positive(
        as_si(viscosity, DYNAMIC_VISCOSITY, "viscosity"), "viscosity"
    )
    cd = validate_positive(discharge_coefficient, "discharge_coefficient")
    if cd > 1:
        raise InvalidInputError("discharge_coefficient must be <= 1.")
    n = hole_count(count)
    area = mdot / (cd * math.sqrt(2 * rho * dp))
    diameter = math.sqrt(4 * area / (math.pi * n))
    velocity = mdot / (rho * area)
    values = (area, diameter, velocity, rho * velocity * diameter / mu, mdot * velocity)
    if not all(math.isfinite(v) and v > 0 for v in values):
        raise InvalidInputError(
            "Orifice sizing overflow/underflow; rescale the inputs."
        )
    return OrificeSizing(
        mdot, area, area / n, diameter, velocity, values[3], values[4], n
    )
