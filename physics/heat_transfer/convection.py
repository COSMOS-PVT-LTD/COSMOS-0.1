"""
COSMOS Rocket Propulsion Platform

Module: physics.heat_transfer.convection
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Newton's law of cooling.
"""

from __future__ import annotations

from core.dimension import AREA, TEMPERATURE
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import HEAT_TRANSFER_COEFFICIENT

__all__ = ("CONVECTION", "newtons_law")

CONVECTION = ModelIdentity(
    model_id="PHYS-005.convection.newton",
    model_name="Newton's law of cooling",
    physical_domain="heat_transfer",
    equations=("q = h A (T_s - T_inf)",),
    inputs=("h [W/(m2 K)]", "A [m2]", "T_s [K]", "T_inf [K]"),
    outputs=("q [W]",),
    assumptions=("Defined h; not a turbulence closure.",),
    validity_range="h > 0; A > 0; T > 0",
    source="Incropera et al., Fundamentals of Heat and Mass Transfer.",
    verification_status="analytical_verification: q=0 when ΔT=0",
    limitations=("h must come from a named correlation (for example Bartz).",),
)


def newtons_law(
    heat_transfer_coefficient: Quantity,
    area: Quantity,
    surface_temperature: Quantity,
    fluid_temperature: Quantity,
) -> Quantity:
    """Return q = h A (Ts - T∞)."""

    h = validate_positive(
        as_si(heat_transfer_coefficient, HEAT_TRANSFER_COEFFICIENT, "h"),
        "h",
    )
    a = validate_positive(as_si(area, AREA, "area"), "area")
    ts = validate_positive(
        as_si(surface_temperature, TEMPERATURE, "surface_temperature"),
        "T_s",
    )
    tinf = validate_positive(
        as_si(fluid_temperature, TEMPERATURE, "fluid_temperature"),
        "T_inf",
    )
    return quantity(h * a * (ts - tinf), SI.get("W"))
