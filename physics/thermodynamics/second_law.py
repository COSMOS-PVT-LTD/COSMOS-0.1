"""
COSMOS Rocket Propulsion Platform

Module: physics.thermodynamics.second_law
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Second-law entropy production statements.
"""

from __future__ import annotations

from core.dimension import ENERGY, TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import Unit
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity

__all__ = (
    "SECOND_LAW",
    "entropy_production_closed",
    "is_possible_process",
)

_ENTROPY_UNIT = Unit("J/K", "joule per kelvin", ENERGY / TEMPERATURE)

SECOND_LAW = ModelIdentity(
    model_id="PHYS-001.second_law.clausius",
    model_name="Second law (Clausius / entropy production)",
    physical_domain="thermodynamics",
    equations=("sigma = Delta S - Q/T", "sigma >= 0"),
    inputs=("delta_entropy [J/K]", "heat_in [J]", "boundary_temperature [K]"),
    outputs=("entropy_production [J/K]",),
    assumptions=(
        "Single thermal reservoir at the boundary temperature for Q/T.",
        "Heat-in sign convention consistent with the first law.",
    ),
    validity_range="T > 0 K; finite entropy and heat.",
    source="Clausius inequality; Cengel & Boles; Moran & Shapiro.",
    verification_status="analytical_verification: reversible σ=0; isolated adiabatic σ=ΔS",
    limitations=(
        "Does not replace availability/exergy analysis for work potential.",
    ),
)


def entropy_production_closed(
    delta_entropy: Quantity,
    heat_in: Quantity,
    boundary_temperature: Quantity,
) -> Quantity:
    """Return σ = ΔS - Q/T for a closed system with one boundary temperature."""

    ds = as_si(delta_entropy, ENERGY / TEMPERATURE, "delta_entropy")
    q = as_si(heat_in, ENERGY, "heat_in")
    t = validate_positive(
        as_si(boundary_temperature, TEMPERATURE, "boundary_temperature"),
        "boundary_temperature",
    )
    return quantity(ds - q / t, _ENTROPY_UNIT)


def is_possible_process(
    entropy_production: Quantity,
    *,
    tolerance: float = 1.0e-12,
) -> bool:
    """Return True when σ >= -tolerance (second-law admissible)."""

    sigma = as_si(entropy_production, ENERGY / TEMPERATURE, "entropy_production")
    if tolerance < 0.0:
        raise InvalidInputError("tolerance must be non-negative.")
    return sigma >= -tolerance
