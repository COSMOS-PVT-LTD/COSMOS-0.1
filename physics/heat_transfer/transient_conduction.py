"""
COSMOS Rocket Propulsion Platform

Module: physics.heat_transfer.transient_conduction
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Lumped-capacitance transient cooling.

Description:
    Valid when Bi = h L / k << 1 (COSMOS uses Bi < 0.1).

        (T - T_inf) / (T_i - T_inf) = exp(-h A t / (ρ V c))

Sources
-------
    Incropera et al., lumped-capacitance method.
"""

from __future__ import annotations

import math

from core.dimension import AREA, DENSITY, LENGTH, TEMPERATURE, TIME, VOLUME
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_non_negative, validate_positive

from physics.exceptions import OutOfRangeError
from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import HEAT_TRANSFER_COEFFICIENT, SPECIFIC_HEAT, THERMAL_CONDUCTIVITY

__all__ = ("LUMPED", "biot_number", "lumped_temperature")

LUMPED = ModelIdentity(
    model_id="PHYS-005.transient.lumped_capacitance",
    model_name="Lumped-capacitance transient conduction",
    physical_domain="heat_transfer",
    equations=(
        "Bi = h L / k",
        "(T-Tinf)/(Ti-Tinf) = exp(-h A t / (rho V c))",
    ),
    inputs=("h", "L", "k", "A", "V", "rho", "c", "t", "Ti", "Tinf"),
    outputs=("T [K]", "Bi [-]"),
    assumptions=("Spatially uniform solid temperature; Bi < 0.1.",),
    validity_range="Bi < 0.1; t >= 0; positive properties",
    source="Incropera et al., lumped-capacitance method.",
    verification_status="analytical_verification: t=0 => T=Ti; Bi definition",
    limitations=("Not a 1D Heisler-chart solution.",),
)


def biot_number(
    heat_transfer_coefficient: Quantity,
    characteristic_length: Quantity,
    conductivity: Quantity,
) -> float:
    """Return Bi = h L / k."""

    h = validate_positive(as_si(heat_transfer_coefficient, HEAT_TRANSFER_COEFFICIENT, "h"), "h")
    length = validate_positive(as_si(characteristic_length, LENGTH, "L"), "L")
    k = validate_positive(as_si(conductivity, THERMAL_CONDUCTIVITY, "k"), "k")
    return h * length / k


def lumped_temperature(
    heat_transfer_coefficient: Quantity,
    area: Quantity,
    volume: Quantity,
    density: Quantity,
    specific_heat: Quantity,
    time: Quantity,
    initial_temperature: Quantity,
    fluid_temperature: Quantity,
    characteristic_length: Quantity,
    conductivity: Quantity,
) -> Quantity:
    """Return T(t) for a lumped body, rejecting Bi >= 0.1."""

    bi = biot_number(heat_transfer_coefficient, characteristic_length, conductivity)
    if bi >= 0.1:
        raise OutOfRangeError(
            f"lumped capacitance requires Bi < 0.1. Received Bi={bi}."
        )
    h = as_si(heat_transfer_coefficient, HEAT_TRANSFER_COEFFICIENT, "h")
    a = validate_positive(as_si(area, AREA, "area"), "area")
    vol = validate_positive(as_si(volume, VOLUME, "volume"), "volume")
    rho = validate_positive(as_si(density, DENSITY, "density"), "density")
    cp = validate_positive(as_si(specific_heat, SPECIFIC_HEAT, "cp"), "cp")
    t = validate_non_negative(as_si(time, TIME, "time"), "time")
    ti = validate_positive(as_si(initial_temperature, TEMPERATURE, "T_i"), "T_i")
    tinf = validate_positive(as_si(fluid_temperature, TEMPERATURE, "T_inf"), "T_inf")
    if rho * vol * cp == 0.0:
        raise InvalidInputError("thermal capacitance is zero.")
    temperature = tinf + (ti - tinf) * math.exp(-h * a * t / (rho * vol * cp))
    return quantity(temperature, SI.get("K"))
