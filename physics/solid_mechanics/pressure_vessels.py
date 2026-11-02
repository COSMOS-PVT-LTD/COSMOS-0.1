"""
COSMOS Rocket Propulsion Platform

Module: physics.solid_mechanics.pressure_vessels
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Thin-wall and Lamé elastic pressure-cylinder stresses (not code design).

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
from math import isfinite, sqrt

from core.dimension import LENGTH, PRESSURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.validation import validate_positive
from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import UNIT_STRESS

__all__ = (
    "LAME_CLOSED_ENDS",
    "THIN_WALL",
    "LameCylinderStress",
    "ThinWallCylinder",
    "cylinder",
    "lame_closed_cylinder",
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
        "Thick walls require the separately selected Lamé model, not this relation.",
    ),
)

LAME_CLOSED_ENDS = ModelIdentity(
    model_id="PHYS-007.pressure_vessel.lame_closed_ends",
    model_name="Lamé elastic smooth cylinder with pressure-loaded closed ends",
    physical_domain="solid_mechanics",
    equations=("sigma_r=A-B/r^2", "sigma_theta=A+B/r^2", "sigma_z=A",
               "A=(Pi*a^2-Po*b^2)/(b^2-a^2)", "B=(Pi-Po)*a^2*b^2/(b^2-a^2)"),
    inputs=("Pi [Pa absolute]", "Po [Pa absolute]", "a [m]", "t [m]", "r [m]"),
    outputs=("radial [Pa]", "hoop [Pa]", "axial [Pa]", "von_mises [Pa]"),
    assumptions=("Long homogeneous isotropic smooth elastic cylinder; small strain.",
                 "Uniform pressures; closed ends carry pressure thrust; away from discontinuities."),
    validity_range="Pi,Po>=0; a,t>0; a<=r<=a+t; elastic small-strain solution only",
    source="NPTEL Solid Mechanics 7.4.1, eqs 7.66-7.69 (radial/hoop); closed-end force balance for axial stress.",
    verification_status="analytical_verification: traction, equilibrium, closed-end force, hydrostatic and thin-wall limits",
    limitations=("No buckling/stability, plasticity, thermal gradients, creep or fatigue.",
                 "No channels, holes, bimetallic interfaces, welds, end closures or nozzle loads.",
                 "Not pressure-vessel-code or hardware qualification."),
)


@dataclass(frozen=True, slots=True)
class LameCylinderStress:
    """Principal stresses at the requested radial station; tension positive."""

    radial: Quantity
    hoop: Quantity
    longitudinal: Quantity
    von_mises: Quantity
    station_radius_m: float
    radius_to_thickness: float
    identity: ModelIdentity = LAME_CLOSED_ENDS


def lame_closed_cylinder(
    internal_pressure: Quantity, external_pressure: Quantity,
    inner_radius: Quantity, wall_thickness: Quantity, *,
    station_radius: Quantity | None = None,
) -> LameCylinderStress:
    """Evaluate a smooth-cylinder elastic field; default station is the bore.

    Pressures are absolute. This elementary field does not assess stability or
    elastic admissibility, even when external pressure exceeds internal pressure.
    """
    pi = as_si(internal_pressure, PRESSURE, "internal_pressure")
    po = as_si(external_pressure, PRESSURE, "external_pressure")
    a = validate_positive(as_si(inner_radius, LENGTH, "inner_radius"), "inner_radius")
    t = validate_positive(as_si(wall_thickness, LENGTH, "wall_thickness"), "wall_thickness")
    b = a + t
    r = a if station_radius is None else as_si(station_radius, LENGTH, "station_radius")
    if not all(isfinite(value) for value in (pi, po, a, t, b, r)):
        raise InvalidInputError("Lamé pressures and dimensions must be finite.")
    if pi < 0 or po < 0 or b <= a or not a <= r <= b:
        raise InvalidInputError("Require nonnegative absolute pressures, resolved wall thickness and a<=r<=a+t.")
    # Factor the difference of squares to avoid cancellation in thin-wall tests.
    denominator = t * (b + a)
    if not isfinite(denominator) or denominator <= 0:
        raise InvalidInputError("Lamé wall dimensions exceed the resolved numerical range.")
    axial = -po + (pi - po) * a * a / denominator
    deviator = (pi - po) * (a / r) ** 2 * b * b / denominator
    values = (axial - deviator, axial + deviator, axial, sqrt(3.0) * abs(deviator))
    if not all(isfinite(value) for value in values):
        raise InvalidInputError("Lamé stress overflow; rescale the specified inputs.")
    return LameCylinderStress(radial=quantity(values[0], UNIT_STRESS),
                              hoop=quantity(values[1], UNIT_STRESS),
                              longitudinal=quantity(values[2], UNIT_STRESS),
                              von_mises=quantity(values[3], UNIT_STRESS),
                              station_radius_m=r, radius_to_thickness=a / t)


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
