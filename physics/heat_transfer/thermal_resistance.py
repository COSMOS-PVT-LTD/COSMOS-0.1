"""
COSMOS Rocket Propulsion Platform

Module: physics.heat_transfer.thermal_resistance
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Thermal-resistance network primitives.
"""

from __future__ import annotations

from core.dimension import AREA, LENGTH, POWER, TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import Unit
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import HEAT_TRANSFER_COEFFICIENT, THERMAL_CONDUCTIVITY

__all__ = (
    "RESISTANCE",
    "conduction_resistance",
    "convection_resistance",
    "series_resistance",
)

_R_UNIT = Unit("K/W", "kelvin per watt", TEMPERATURE / POWER)

RESISTANCE = ModelIdentity(
    model_id="PHYS-005.resistance.network",
    model_name="Thermal resistance primitives",
    physical_domain="heat_transfer",
    equations=("R_cond = L/(k A)", "R_conv = 1/(h A)", "q = Delta T / R_total"),
    inputs=("k [W/(m K)]", "h [W/(m2 K)]", "A [m2]", "L [m]"),
    outputs=("R [K/W]",),
    assumptions=("Lumped 1D resistances; isothermal nodes.",),
    validity_range="positive properties and area",
    source="Incropera et al., thermal-resistance networks.",
    verification_status="analytical_verification: series sum; q=ΔT/R",
    limitations=("Not a 2D conduction FEM.",),
)


def conduction_resistance(
    thickness: Quantity,
    conductivity: Quantity,
    area: Quantity,
) -> Quantity:
    """Return R_cond = L / (k A)."""

    length = validate_positive(as_si(thickness, LENGTH, "thickness"), "thickness")
    k = validate_positive(as_si(conductivity, THERMAL_CONDUCTIVITY, "k"), "k")
    a = validate_positive(as_si(area, AREA, "area"), "area")
    return quantity(length / (k * a), _R_UNIT)


def convection_resistance(
    heat_transfer_coefficient: Quantity,
    area: Quantity,
) -> Quantity:
    """Return R_conv = 1 / (h A)."""

    h = validate_positive(
        as_si(heat_transfer_coefficient, HEAT_TRANSFER_COEFFICIENT, "h"),
        "h",
    )
    a = validate_positive(as_si(area, AREA, "area"), "area")
    return quantity(1.0 / (h * a), _R_UNIT)


def series_resistance(resistances: tuple[Quantity, ...]) -> Quantity:
    """Return the sum of series thermal resistances."""

    if not resistances:
        raise InvalidInputError("resistances must not be empty.")
    total = 0.0
    for item in resistances:
        total += as_si(item, TEMPERATURE / POWER, "resistance")
    return quantity(total, _R_UNIT)
