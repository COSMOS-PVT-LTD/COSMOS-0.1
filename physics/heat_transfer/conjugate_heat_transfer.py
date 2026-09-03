"""
COSMOS Rocket Propulsion Platform

Module: physics.heat_transfer.conjugate_heat_transfer
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Conjugate gas-wall-coolant resistance chain (1D).

Description:
    Assembles Newton's law, wall conduction, and coolant convection
    as a series resistance. Does not run a CHT CFD solver.
"""

from __future__ import annotations

from core.dimension import TEMPERATURE
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive

from physics.heat_transfer.thermal_resistance import series_resistance
from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import HEAT_FLUX

__all__ = ("CONJUGATE_1D", "wall_heat_flux")

CONJUGATE_1D = ModelIdentity(
    model_id="PHYS-005.cht.series_resistance",
    model_name="1D conjugate gas-wall-coolant chain",
    physical_domain="heat_transfer",
    equations=("q = (T_gas - T_coolant) / (R_gas + R_wall + R_coolant)",),
    inputs=("T_gas [K]", "T_coolant [K]", "resistances [K/W]"),
    outputs=("q [W]",),
    assumptions=("Steady 1D; isothermal fluid nodes.",),
    validity_range="positive resistances; T > 0",
    source="Incropera thermal-resistance networks applied to a cooled wall.",
    verification_status="analytical_verification: series resistance energy balance",
    limitations=("Not a 2D/3D conjugate CFD coupling.",),
)


def wall_heat_rate(
    gas_temperature: Quantity,
    coolant_temperature: Quantity,
    gas_resistance: Quantity,
    wall_resistance: Quantity,
    coolant_resistance: Quantity,
) -> Quantity:
    """Return heat rate through a 1D conjugate wall [W]."""

    t_g = validate_positive(as_si(gas_temperature, TEMPERATURE, "T_gas"), "T_gas")
    t_c = validate_positive(
        as_si(coolant_temperature, TEMPERATURE, "T_coolant"),
        "T_coolant",
    )
    r_total = series_resistance((gas_resistance, wall_resistance, coolant_resistance))
    r = r_total.to_si()
    return quantity((t_g - t_c) / r, SI.get("W"))


def wall_heat_flux(*_args: object, **_kwargs: object) -> Quantity:
    """Heat-flux form requires area; use wall_heat_rate / area at the caller."""

    from physics.exceptions import InsufficientDataError

    raise InsufficientDataError(
        "Use wall_heat_rate and divide by the local area. A flux form "
        "without area would hide the resistance definition."
    )


_ = HEAT_FLUX
