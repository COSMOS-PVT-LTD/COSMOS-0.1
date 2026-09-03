"""
COSMOS Rocket Propulsion Platform

Module: physics.solid_mechanics.stress
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Stress measures: uniaxial, principal (2D), von Mises.
"""

from __future__ import annotations

import math

from core.dimension import AREA, FORCE, PRESSURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import UNIT_STRESS

__all__ = (
    "STRESS",
    "normal_stress",
    "principal_stress_2d",
    "von_mises",
)

STRESS = ModelIdentity(
    model_id="PHYS-007.stress.measures",
    model_name="Stress measures",
    physical_domain="solid_mechanics",
    equations=(
        "sigma = F / A",
        "sigma_1,2 = (sx+sy)/2 ± sqrt(((sx-sy)/2)^2 + txy^2)",
        "sigma_vm = sqrt(0.5*((s1-s2)^2+(s2-s3)^2+(s3-s1)^2))",
    ),
    inputs=("force [N]", "area [m2]", "principal stresses [Pa]"),
    outputs=("stress [Pa]",),
    assumptions=("Continuum; small-deformation stress measures.",),
    validity_range="A > 0",
    source="Shigley, Mechanical Engineering Design; continuum mechanics definitions.",
    verification_status="analytical_verification: hydrostatic von Mises=0; uniaxial VM=|σ|",
    limitations=("Not a finite-element stress solver.",),
)


def normal_stress(force: Quantity, area: Quantity) -> Quantity:
    """Return σ = F / A."""

    f = as_si(force, FORCE, "force")
    a = validate_positive(as_si(area, AREA, "area"), "area")
    return quantity(f / a, UNIT_STRESS)


def principal_stress_2d(
    sigma_x: Quantity,
    sigma_y: Quantity,
    tau_xy: Quantity,
) -> tuple[float, float]:
    """Return (σ1, σ2) for plane stress, σ1 >= σ2, in pascal."""

    sx = as_si(sigma_x, PRESSURE, "sigma_x")
    sy = as_si(sigma_y, PRESSURE, "sigma_y")
    txy = as_si(tau_xy, PRESSURE, "tau_xy")
    center = 0.5 * (sx + sy)
    radius = math.sqrt(((sx - sy) * 0.5) ** 2 + txy * txy)
    return (center + radius, center - radius)


def von_mises(sigma_1: float, sigma_2: float, sigma_3: float = 0.0) -> Quantity:
    """Return the von Mises equivalent stress."""

    for name, value in (("s1", sigma_1), ("s2", sigma_2), ("s3", sigma_3)):
        if not math.isfinite(value):
            raise InvalidInputError(f"{name} must be finite.")
    vm = math.sqrt(
        0.5
        * (
            (sigma_1 - sigma_2) ** 2
            + (sigma_2 - sigma_3) ** 2
            + (sigma_3 - sigma_1) ** 2
        )
    )
    return quantity(vm, UNIT_STRESS)
