"""
COSMOS Rocket Propulsion Platform

Module: physics.heat_transfer.conduction
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Fourier conduction (plane wall).

Description:
    q = k A (T_hot - T_cold) / L
    R_cond = L / (k A)

Sources
-------
    Incropera, DeWitt, Bergman, Lavine, Fundamentals of Heat and Mass Transfer.
"""

from __future__ import annotations

from core.dimension import AREA, LENGTH, TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import THERMAL_CONDUCTIVITY, UNIT_HEAT_FLUX

__all__ = ("CONDUCTION", "plane_wall_heat_rate", "heat_flux")

CONDUCTION = ModelIdentity(
    model_id="PHYS-005.conduction.fourier_plane_wall",
    model_name="Fourier plane-wall conduction",
    physical_domain="heat_transfer",
    equations=("q = k A (T_h - T_c) / L",),
    inputs=("k [W/(m K)]", "A [m2]", "L [m]", "T_h [K]", "T_c [K]"),
    outputs=("q [W]",),
    assumptions=("Steady; one-dimensional; constant k; no generation.",),
    validity_range="k > 0; A > 0; L > 0; T > 0",
    source="Incropera et al., Fundamentals of Heat and Mass Transfer (Fourier's law).",
    verification_status="analytical_verification: q=0 when ΔT=0; dimensions W",
    limitations=("Not a 2D/3D conduction solver.",),
)


def plane_wall_heat_rate(
    conductivity: Quantity,
    area: Quantity,
    thickness: Quantity,
    hot_temperature: Quantity,
    cold_temperature: Quantity,
) -> Quantity:
    """Return q [W] through a plane wall."""

    k = validate_positive(as_si(conductivity, THERMAL_CONDUCTIVITY, "conductivity"), "k")
    a = validate_positive(as_si(area, AREA, "area"), "area")
    length = validate_positive(as_si(thickness, LENGTH, "thickness"), "thickness")
    th = validate_positive(as_si(hot_temperature, TEMPERATURE, "hot_temperature"), "T_hot")
    tc = validate_positive(as_si(cold_temperature, TEMPERATURE, "cold_temperature"), "T_cold")
    return quantity(k * a * (th - tc) / length, SI.get("W"))


def heat_flux(
    conductivity: Quantity,
    thickness: Quantity,
    hot_temperature: Quantity,
    cold_temperature: Quantity,
) -> Quantity:
    """Return q'' = k ΔT / L."""

    k = validate_positive(as_si(conductivity, THERMAL_CONDUCTIVITY, "conductivity"), "k")
    length = validate_positive(as_si(thickness, LENGTH, "thickness"), "thickness")
    th = validate_positive(as_si(hot_temperature, TEMPERATURE, "hot_temperature"), "T_hot")
    tc = validate_positive(as_si(cold_temperature, TEMPERATURE, "cold_temperature"), "T_cold")
    if length == 0.0:
        raise InvalidInputError("thickness must be positive.")
    return quantity(k * (th - tc) / length, UNIT_HEAT_FLUX)
