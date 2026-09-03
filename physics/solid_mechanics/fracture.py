"""
COSMOS Rocket Propulsion Platform

Module: physics.solid_mechanics.fracture
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Mode-I stress-intensity for a through-crack in an infinite plate.

Description:
    K_I = Y σ sqrt(π a) with Y = 1 for the infinite-plate through-crack.

    Geometry factors Y ≠ 1 are not invented.
"""

from __future__ import annotations

import math

from core.constants import PI
from core.dimension import LENGTH, PRESSURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import Unit
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si

__all__ = ("FRACTURE", "K_I_UNIT", "mode_i_infinite_plate")

_K_UNIT = Unit("Pa m^0.5", "pascal metre to the half", PRESSURE * (LENGTH**0))
K_I_UNIT = _K_UNIT

# K has dimension stress * sqrt(length). Core Dimension only supports integer
# exponents, so the unit is documented and the SI magnitude is Pa * sqrt(m).
# OPEN SCIENTIFIC ISSUE / CORE-CONTRACT-ISSUE: half-integer dimensions.

FRACTURE = ModelIdentity(
    model_id="PHYS-007.fracture.mode_i_infinite_plate",
    model_name="Mode-I stress intensity, infinite plate",
    physical_domain="solid_mechanics",
    equations=("K_I = sigma * sqrt(pi * a)   (Y=1)",),
    inputs=("sigma [Pa]", "a [m]"),
    outputs=("K_I [Pa sqrt(m)]",),
    assumptions=("Infinite plate; through-crack; linear elastic fracture mechanics.",),
    validity_range="sigma finite; a > 0",
    source="Shigley / LEFM textbook definition of K_I for Y=1.",
    verification_status="analytical_verification: K scales as sqrt(a)",
    limitations=(
        "Y≠1 geometries are OPEN SCIENTIFIC ISSUE without a sourced handbook factor.",
        "Core Dimension cannot represent sqrt(L); magnitude is SI Pa*sqrt(m).",
    ),
)


def mode_i_infinite_plate(remote_stress: Quantity, crack_length: Quantity) -> float:
    """
    Return K_I [Pa sqrt(m)] for Y = 1.

    The return is a float because Core dimensions are integer exponents.
    """

    sigma = as_si(remote_stress, PRESSURE, "sigma")
    a = validate_positive(as_si(crack_length, LENGTH, "a"), "a")
    if a == 0.0:
        raise InvalidInputError("crack length must be positive.")
    return sigma * math.sqrt(PI * a)
