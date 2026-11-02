"""Exact axial-plane geometry of an annular-sector passage, not flow physics."""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.dimension import DIMENSIONLESS, LENGTH
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.validation import validate_positive
from physics.model import ModelIdentity
from physics.quantities import as_si

SECTOR_PASSAGE = ModelIdentity(
    model_id="PHYS-FLUID.axial_annular_sector_geometry",
    model_name="Axial annular-sector passage geometry",
    physical_domain="fluids",
    equations=("A = theta (b-a)(a+b)/2", "P = theta (a+b)+2(b-a)", "Dh = 4A/P",
               "r_centroid = 4 sin(theta/2) (a²+ab+b²) / (3 theta (a+b))"),
    inputs=("inner/outer radii [m]", "sector angle [rad]"),
    outputs=("axial-plane area [m2]", "wetted perimeter [m]", "axial-plane Dh [m]", "centroid radius [m]"),
    assumptions=("Exact circular arcs and radial sidewalls in an axial plane.",),
    validity_range="0 < inner < outer; 0 < theta < 2pi; finite representable positive geometry",
    source="Direct polar-coordinate area and first-moment integration; hydraulic diameter geometric definition 4A/P.",
    verification_status="analytic limits, polar quadrature, scale laws and domain/dimensional checks",
    limitations=("Not flow-normal geometry on a sloped passage; no friction/heat-transfer correlation or physical validation.",),
)


@dataclass(frozen=True, slots=True)
class SectorSection:
    area_m2: float
    wetted_perimeter_m: float
    hydraulic_diameter_m: float
    centroid_radius_m: float


def annular_sector_section(inner: Quantity, outer: Quantity, angle: Quantity) -> SectorSection:
    """Return A, P, 4A/P and bisector centroid; no empirical duct correlation."""
    a = validate_positive(as_si(inner, LENGTH, "inner radius"), "inner radius")
    b = validate_positive(as_si(outer, LENGTH, "outer radius"), "outer radius")
    theta = validate_positive(as_si(angle, DIMENSIONLESS, "sector angle"), "sector angle")
    if b <= a or theta >= 2 * math.pi:
        raise InvalidInputError("Require outer > inner > 0 and 0 < sector angle < 2pi rad.")
    area = theta * (b - a) * (a + b) / 2
    perimeter = theta * (a + b) + 2 * (b - a)
    # Factor the difference of cubes/squares to avoid thin-section cancellation.
    centroid = (4 / 3 * (math.sin(theta / 2) / theta)
                * (b + a * (a / (a + b))))
    if not math.isfinite(perimeter) or perimeter <= 0:
        raise InvalidInputError("Sector perimeter is outside finite positive numerical bounds.")
    values = (area, perimeter, 4 * area / perimeter, centroid)
    if not all(math.isfinite(v) and v > 0 for v in values):
        raise InvalidInputError("Sector geometry is outside finite positive numerical bounds.")
    return SectorSection(*values)
