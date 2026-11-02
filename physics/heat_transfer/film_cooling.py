"""
COSMOS Rocket Propulsion Platform

Module: physics.heat_transfer.film_cooling
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Explicit gaseous-slot enthalpy-mixing effectiveness estimate.
"""

from __future__ import annotations

from core.dimension import LENGTH, TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.validation import validate_finite, validate_positive
from physics.exceptions import InsufficientDataError
from physics.model import ModelIdentity
from physics.quantities import as_si, kelvin

__all__ = ("FILM_COOLING", "effectiveness", "film_adiabatic_temperature")

FILM_COOLING = ModelIdentity(
    model_id="PHYS-005.film_cooling.goldstein_slot",
    model_name="Gaseous-slot film cooling mixing estimate",
    physical_domain="heat_transfer",
    equations=(
        "xi = 7 delta / (8 F s)",
        "eta_ad = 1 / (1 + (Cp_g/Cp_c) xi)",
        "Taw_f = Taw_g - eta_ad (Taw_g - T_c)",
    ),
    inputs=(
        "boundary layer thickness delta [m]",
        "slot height s [m]",
        "blowing ratio F [-]",
        "heat capacity ratio [-]",
    ),
    outputs=("effectiveness [-]",),
    assumptions=(
        "Gaseous tangential slot, 1/7-power turbulent velocity profile.",
        "Boundary-layer thickness is an explicit, sourced analysis input.",
        "Constant heat capacities; enthalpy mixing with no reaction.",
    ),
    validity_range="Positive delta, s, F and Cp ratio; applicability must be assessed for the actual slot flow.",
    source="Goldstein mixing model as stated in Peter and Kloker (2020), equations 2-3; https://doi.org/10.1007/978-3-030-53847-7_5",
    verification_status="analytical mixing identity and limiting/scaling tests",
    limitations=(
        "Not a universal rocket film correlation; no liquid evaporation, discrete holes, shocks or chemistry.",
        "Accelerating nozzle flow and coupled wall cooling need validation; no DNS-fit coefficients are generalized.",
    ),
)


def effectiveness(
    *,
    boundary_layer_thickness: Quantity | None = None,
    slot_height: Quantity | None = None,
    blowing_ratio: float | None = None,
    heat_capacity_ratio: float | None = None,
) -> float:
    if any(
        v is None
        for v in (
            boundary_layer_thickness,
            slot_height,
            blowing_ratio,
            heat_capacity_ratio,
        )
    ):
        raise InsufficientDataError(
            "Film cooling requires explicit delta, slot height, blowing ratio and heat capacity ratio."
        )
    assert boundary_layer_thickness is not None and slot_height is not None
    assert blowing_ratio is not None and heat_capacity_ratio is not None
    delta = validate_positive(as_si(boundary_layer_thickness, LENGTH, "delta"), "delta")
    height = validate_positive(as_si(slot_height, LENGTH, "slot_height"), "slot_height")
    blowing = validate_positive(blowing_ratio, "blowing_ratio")
    cp_ratio = validate_positive(heat_capacity_ratio, "heat_capacity_ratio")
    xi = 7 * delta / (8 * blowing * height)
    value = validate_finite(1 / (1 + cp_ratio * xi), "film effectiveness")
    if not 0 < value < 1:
        raise InvalidInputError("Film mixing estimate is numerically degenerate.")
    return value


def film_adiabatic_temperature(
    gas_temperature: Quantity, coolant_temperature: Quantity, eta: float
) -> Quantity:
    gas = validate_positive(
        as_si(gas_temperature, TEMPERATURE, "gas_temperature"), "gas_temperature"
    )
    coolant = validate_positive(
        as_si(coolant_temperature, TEMPERATURE, "coolant_temperature"),
        "coolant_temperature",
    )
    value = validate_finite(eta, "eta")
    if not 0 <= value <= 1 or coolant > gas:
        raise InvalidInputError(
            "Require 0 <= eta <= 1 and coolant temperature <= gas temperature."
        )
    return kelvin(gas - value * (gas - coolant))
