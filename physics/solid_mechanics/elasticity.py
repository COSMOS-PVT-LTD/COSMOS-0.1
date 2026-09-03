"""
COSMOS Rocket Propulsion Platform

Module: physics.solid_mechanics.elasticity
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Hooke's law and isotropic elastic identities.
"""

from __future__ import annotations

from core.dimension import PRESSURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.validation import validate_positive, validate_range

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import UNIT_STRESS

__all__ = ("HOOKE", "uniaxial_stress", "shear_modulus")

HOOKE = ModelIdentity(
    model_id="PHYS-007.elasticity.hooke",
    model_name="Isotropic Hooke's law (uniaxial)",
    physical_domain="solid_mechanics",
    equations=("sigma = E * epsilon", "G = E / (2 (1+nu))"),
    inputs=("E [Pa]", "epsilon [-]", "nu [-]"),
    outputs=("sigma [Pa]", "G [Pa]"),
    assumptions=("Linear isotropic elasticity; small strain.",),
    validity_range="E > 0; -1 < nu < 0.5",
    source="Shigley, Mechanical Engineering Design (elastic relations).",
    verification_status="analytical_verification: G identity; uniaxial Hooke",
    limitations=("Not a plastic constitutive model.",),
)


def uniaxial_stress(youngs_modulus: Quantity, strain: float) -> Quantity:
    """Return σ = E ε."""

    e = validate_positive(as_si(youngs_modulus, PRESSURE, "E"), "E")
    if not abs(strain) < 1.0e6:
        raise InvalidInputError("strain is non-finite or implausible.")
    return quantity(e * strain, UNIT_STRESS)


def shear_modulus(youngs_modulus: Quantity, poisson_ratio: float) -> Quantity:
    """Return G = E / (2 (1+ν))."""

    e = validate_positive(as_si(youngs_modulus, PRESSURE, "E"), "E")
    nu = validate_range(poisson_ratio, -0.99, 0.499, "poisson_ratio")
    return quantity(e / (2.0 * (1.0 + nu)), UNIT_STRESS)
