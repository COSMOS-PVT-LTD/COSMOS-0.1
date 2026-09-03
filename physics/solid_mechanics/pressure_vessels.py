"""
COSMOS Rocket Propulsion Platform

Module: physics.solid_mechanics.pressure_vessels
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Thin-wall pressure-vessel membrane stresses (physics, not ASME design).

Description:
    Closed cylinder:
        σ_h = p r / t
        σ_l = p r / (2 t)
    Sphere:
        σ = p r / (2 t)

    These are physical membrane relations (Roark / continuum). They are
    not a pressure-vessel design code.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.dimension import LENGTH, PRESSURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import UNIT_STRESS

__all__ = (
    "THIN_WALL",
    "ThinWallCylinder",
    "cylinder",
    "sphere",
)

THIN_WALL = ModelIdentity(
    model_id="PHYS-007.pressure_vessel.thin_wall",
    model_name="Thin-wall membrane stresses",
    physical_domain="solid_mechanics",
    equations=("sigma_h = p r / t", "sigma_l = p r / (2 t)", "sigma_sph = p r / (2 t)"),
    inputs=("p [Pa]", "r [m]", "t [m]"),
    outputs=("stress [Pa]",),
    assumptions=("Thin wall (r/t typically > 10); membrane theory; no discontinuities.",),
    validity_range="p >= 0; r > 0; t > 0; r/t >= 10 for the thin-wall assumption",
    source="Roark's Formulas for Stress and Strain; Shigley (thin-wall vessels).",
    verification_status="analytical_verification: sphere vs cylinder hoop/long; dimensions",
    limitations=(
        "Not ASME BPVC, not PED, not a design-by-analysis workflow.",
        "Thick-wall Lamé solution is not implemented in this batch.",
    ),
)


@dataclass(frozen=True, slots=True)
class ThinWallCylinder:
    """Hoop and longitudinal membrane stresses."""

    hoop: Quantity
    longitudinal: Quantity
    radius_to_thickness: float
    identity: ModelIdentity = THIN_WALL


def cylinder(pressure: Quantity, inner_radius: Quantity, wall_thickness: Quantity) -> ThinWallCylinder:
    """Return thin-wall cylinder stresses."""

    p = as_si(pressure, PRESSURE, "pressure")
    if p < 0.0:
        raise InvalidInputError("pressure must be non-negative.")
    r = validate_positive(as_si(inner_radius, LENGTH, "inner_radius"), "r")
    t = validate_positive(as_si(wall_thickness, LENGTH, "wall_thickness"), "t")
    ratio = r / t
    hoop = p * r / t
    long = p * r / (2.0 * t)
    return ThinWallCylinder(
        hoop=quantity(hoop, UNIT_STRESS),
        longitudinal=quantity(long, UNIT_STRESS),
        radius_to_thickness=ratio,
    )


def sphere(pressure: Quantity, inner_radius: Quantity, wall_thickness: Quantity) -> Quantity:
    """Return thin-wall spherical membrane stress."""

    p = as_si(pressure, PRESSURE, "pressure")
    if p < 0.0:
        raise InvalidInputError("pressure must be non-negative.")
    r = validate_positive(as_si(inner_radius, LENGTH, "inner_radius"), "r")
    t = validate_positive(as_si(wall_thickness, LENGTH, "wall_thickness"), "t")
    return quantity(p * r / (2.0 * t), UNIT_STRESS)
