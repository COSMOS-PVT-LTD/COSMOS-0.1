"""
COSMOS Rocket Propulsion Platform

Module: physics.heat_transfer.heat_flux
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Convective heat flux q'' = h (T_aw - T_w).
"""

from __future__ import annotations

from core.dimension import TEMPERATURE
from core.quantity import Quantity
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import HEAT_TRANSFER_COEFFICIENT, UNIT_HEAT_FLUX

__all__ = ("HEAT_FLUX", "convective_heat_flux")

HEAT_FLUX = ModelIdentity(
    model_id="PHYS-005.heat_flux.convective",
    model_name="Convective wall heat flux",
    physical_domain="heat_transfer",
    equations=("q_dot = h * (T_aw - T_w)",),
    inputs=("h [W/(m2 K)]", "T_aw [K]", "T_w [K]"),
    outputs=("q_dot [W/m2]",),
    assumptions=("Newton cooling with recovery/adiabatic-wall temperature.",),
    validity_range="h > 0; T > 0",
    source="Incropera et al.; Bartz/Huzel rocket thermal chain.",
    verification_status="analytical_verification: q=0 when T_aw=T_w",
    limitations=("Does not include radiation or film-cooling reduction.",),
)


def convective_heat_flux(
    heat_transfer_coefficient: Quantity,
    adiabatic_wall_temperature: Quantity,
    wall_temperature: Quantity,
) -> Quantity:
    """Return q'' = h (T_aw - T_w)."""

    h = validate_positive(
        as_si(heat_transfer_coefficient, HEAT_TRANSFER_COEFFICIENT, "h"),
        "h",
    )
    taw = validate_positive(
        as_si(adiabatic_wall_temperature, TEMPERATURE, "T_aw"),
        "T_aw",
    )
    tw = validate_positive(as_si(wall_temperature, TEMPERATURE, "T_w"), "T_w")
    return quantity(h * (taw - tw), UNIT_HEAT_FLUX)
