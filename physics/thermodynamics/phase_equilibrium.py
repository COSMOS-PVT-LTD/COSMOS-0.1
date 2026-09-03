"""
COSMOS Rocket Propulsion Platform

Module: physics.thermodynamics.phase_equilibrium
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Clausius–Clapeyron relation without unsourced latent heats.

Description:
    Differential Clausius–Clapeyron equation:

        dp/dT = h_fg / (T * v_fg)

    Integrated approximate form (constant h_fg, ideal vapor):

        ln(p2/p1) = (h_fg / R) * (1/T1 - 1/T2)

    Latent heats and saturation curves are fluid-specific. This module
    evaluates the relation when those properties are supplied; it does
    not invent saturation data.
"""

from __future__ import annotations

import math

from core.dimension import MASS, PRESSURE, TEMPERATURE, VOLUME
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import Unit
from core.validation import validate_positive

from physics.exceptions import InsufficientDataError
from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import SPECIFIC_ENERGY, SPECIFIC_HEAT

__all__ = (
    "CLAUSIUS_CLAPEYRON",
    "slope",
    "integrated_pressure_ratio",
    "saturation_pressure",
)

_SPECIFIC_VOLUME = VOLUME / MASS
_DP_DT_UNIT = Unit("Pa/K", "pascal per kelvin", PRESSURE / TEMPERATURE)

CLAUSIUS_CLAPEYRON = ModelIdentity(
    model_id="PHYS-001.phase.clausius_clapeyron",
    model_name="Clausius-Clapeyron relation",
    physical_domain="thermodynamics",
    equations=(
        "dp/dT = h_fg / (T * v_fg)",
        "ln(p2/p1) = (h_fg / R) * (1/T1 - 1/T2)",
    ),
    inputs=("h_fg [J/kg]", "T [K]", "v_fg [m3/kg]"),
    outputs=("dp_dT [Pa/K]",),
    assumptions=(
        "Two-phase equilibrium.",
        "Integrated form assumes constant h_fg and ideal vapor.",
    ),
    validity_range="T > 0 K; away from the critical point (v_fg → 0 is singular).",
    source="Cengel & Boles; Moran & Shapiro (phase-change chapter).",
    verification_status="analytical_verification: integrated form consistency",
    limitations=(
        "Does not replace a sourced saturation table.",
        "Invalid at the critical point.",
    ),
)


def slope(
    latent_heat: Quantity,
    temperature: Quantity,
    specific_volume_change: Quantity,
) -> Quantity:
    """Return dp/dT = h_fg / (T v_fg)."""

    h_fg = as_si(latent_heat, SPECIFIC_ENERGY, "latent_heat")
    t = validate_positive(as_si(temperature, TEMPERATURE, "temperature"), "temperature")
    v_fg = as_si(specific_volume_change, _SPECIFIC_VOLUME, "specific_volume_change")
    if v_fg == 0.0:
        raise InvalidInputError(
            "specific_volume_change v_fg is zero; Clausius-Clapeyron is singular."
        )
    return quantity(h_fg / (t * v_fg), _DP_DT_UNIT)


def integrated_pressure_ratio(
    temperature_1: Quantity,
    temperature_2: Quantity,
    latent_heat: Quantity,
    specific_gas_constant: Quantity,
) -> float:
    """
    Return p2/p1 from the integrated Clausius–Clapeyron approximation.
    """

    t1 = validate_positive(as_si(temperature_1, TEMPERATURE, "temperature_1"), "T1")
    t2 = validate_positive(as_si(temperature_2, TEMPERATURE, "temperature_2"), "T2")
    h_fg = as_si(latent_heat, SPECIFIC_ENERGY, "latent_heat")
    r = validate_positive(
        as_si(specific_gas_constant, SPECIFIC_HEAT, "R"),
        "specific_gas_constant",
    )
    return math.exp((h_fg / r) * (1.0 / t1 - 1.0 / t2))


def saturation_pressure(*_args: object, **_kwargs: object) -> Quantity:
    """Saturation pressure tables are fluid-specific and not invented here."""

    raise InsufficientDataError(
        "Saturation-pressure evaluation requires sourced fluid vapor-pressure "
        "data. Use physics.fluids property records when a vapor-pressure "
        "source exists."
    )
