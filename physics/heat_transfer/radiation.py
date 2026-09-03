"""
COSMOS Rocket Propulsion Platform

Module: physics.heat_transfer.radiation
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Net radiation between a gray surface and a large enclosure.
"""

from __future__ import annotations

from core.constants import STEFAN_BOLTZMANN_CONSTANT
from core.dimension import AREA, TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive, validate_range

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity

__all__ = ("RADIATION", "net_heat_rate")

RADIATION = ModelIdentity(
    model_id="PHYS-005.radiation.gray_enclosure",
    model_name="Gray-body net radiation to a large enclosure",
    physical_domain="heat_transfer",
    equations=("q = epsilon * sigma * A * (T_s^4 - T_sur^4)",),
    inputs=("epsilon [-]", "A [m2]", "T_s [K]", "T_sur [K]"),
    outputs=("q [W]",),
    assumptions=("Gray, diffuse surface; large isothermal surroundings; F=1.",),
    validity_range="0 < epsilon <= 1; T > 0",
    source="Incropera et al.; CODATA Stefan-Boltzmann constant via core.constants.",
    verification_status="analytical_verification: T_s=T_sur => q=0",
    limitations=("Not a participating-media radiation solver.",),
)


def net_heat_rate(
    emissivity: float,
    area: Quantity,
    surface_temperature: Quantity,
    surroundings_temperature: Quantity,
) -> Quantity:
    """Return q = ε σ A (Ts^4 - Tsur^4)."""

    eps = validate_range(emissivity, 0.0, 1.0, "emissivity")
    if eps <= 0.0:
        raise InvalidInputError("emissivity must be in (0, 1].")
    a = validate_positive(as_si(area, AREA, "area"), "area")
    ts = validate_positive(as_si(surface_temperature, TEMPERATURE, "T_s"), "T_s")
    tsur = validate_positive(
        as_si(surroundings_temperature, TEMPERATURE, "T_sur"),
        "T_sur",
    )
    q = eps * STEFAN_BOLTZMANN_CONSTANT * a * (ts**4 - tsur**4)
    return quantity(q, SI.get("W"))
