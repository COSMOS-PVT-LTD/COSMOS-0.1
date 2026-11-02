"""Axisymmetric divergent bell geometry; not Rao optimization or axisymmetric MOC."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise

from core.dimension import LENGTH, PRESSURE, TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.validation import validate_positive
from numerics.mesh.parametric_curve import quadratic_bezier
from physics.compressible_flow.area_mach import mach_from_area_ratio
from physics.compressible_flow.isentropic import (
    static_pressure_ratio,
    static_temperature_ratio,
)
from physics.model import ModelIdentity
from physics.quantities import as_si, require_gamma

BELL_CONTOUR = ModelIdentity(
    model_id="PHYS-NOZ.tangent_bell_geometry",
    model_name="Circular throat blend and tangent parabolic bell geometry",
    physical_domain="compressible_flow",
    equations=(
        "Re = Rt sqrt(epsilon)",
        "L = f [Re - Rt + Rb (sec(15 deg)-1)] / tan(15 deg)",
        "x = Rb sin(theta); r = Rt + Rb(1-cos(theta))",
        "P(t) = (1-t)^2 N + 2t(1-t) Q + t^2 E",
    ),
    inputs=(
        "Rt [m]",
        "epsilon [-]",
        "length fraction [-]",
        "start/exit angles [deg]",
        "blend radius / Rt [-]",
        "point count [-]",
    ),
    outputs=("x [m]", "r [m]", "wall angle [deg]", "local area ratio [-]"),
    assumptions=(
        "Axisymmetric geometric construction with user-selected angles and blend radius.",
        "Tangent intersection defines the quadratic parabolic segment.",
    ),
    validity_range="epsilon > 1; 0 < exit angle < start angle < 90 deg; monotonic x and radius",
    numerical_method_dependency="numerics.mesh.parametric_curve.quadratic_bezier",
    source="Huzel and Huang, NASA SP-125, section 4.3, figure 4-13; https://ntrs.nasa.gov/citations/19710019929",
    verification_status="endpoint, area, analytic tangent and discretization tests",
    limitations=(
        "Divergent wall only; no convergent/chamber CAD, thickness or manufacturing tolerances.",
        "Not a Rao optimum, a characteristic net, CFD, separation or side-load analysis.",
        "Quasi-1D station data are not a solution of the 2D flow in this contour.",
    ),
)


@dataclass(frozen=True, slots=True)
class ContourPoint:
    x_m: float
    radius_m: float
    wall_angle_deg: float
    area_ratio: float


@dataclass(frozen=True, slots=True)
class NozzleFlowStation(ContourPoint):
    mach: float
    pressure_pa: float
    temperature_k: float


def flow_stations(
    points: tuple[ContourPoint, ...],
    chamber_pressure: Quantity,
    chamber_temperature: Quantity,
    gamma: float,
) -> tuple[NozzleFlowStation, ...]:
    pc = validate_positive(
        as_si(chamber_pressure, PRESSURE, "chamber_pressure"), "chamber_pressure"
    )
    tc = validate_positive(
        as_si(chamber_temperature, TEMPERATURE, "chamber_temperature"),
        "chamber_temperature",
    )
    g = require_gamma(gamma)
    rows = []
    for point in points:
        mach = mach_from_area_ratio(point.area_ratio, g)
        rows.append(
            NozzleFlowStation(
                point.x_m,
                point.radius_m,
                point.wall_angle_deg,
                point.area_ratio,
                mach,
                pc * static_pressure_ratio(mach, g),
                tc * static_temperature_ratio(mach, g),
            )
        )
    return tuple(rows)


def bell_contour(
    throat_radius: Quantity,
    expansion_ratio: float,
    length_fraction: float,
    start_angle_deg: float,
    exit_angle_deg: float,
    blend_radius_ratio: float,
    point_count: int,
) -> tuple[ContourPoint, ...]:
    rt = validate_positive(
        as_si(throat_radius, LENGTH, "throat_radius"), "throat_radius"
    )
    eps = validate_positive(expansion_ratio, "expansion_ratio")
    fraction = validate_positive(length_fraction, "length_fraction")
    blend = validate_positive(blend_radius_ratio, "blend_radius_ratio") * rt
    tn = math.radians(validate_positive(start_angle_deg, "start_angle_deg"))
    te = math.radians(validate_positive(exit_angle_deg, "exit_angle_deg"))
    if eps <= 1 or not 0 < te < tn < math.pi / 2 or not 0 < fraction <= 1:
        raise InvalidInputError(
            "Require epsilon > 1, 0 < exit < start < 90 degrees and 0 < length fraction <= 1."
        )
    if (
        isinstance(point_count, bool)
        or not isinstance(point_count, int)
        or not 11 <= point_count <= 1001
    ):
        raise InvalidInputError("point_count must be an integer from 11 to 1001.")
    re = rt * math.sqrt(eps)
    reference_angle = math.radians(15)
    length = (
        fraction
        * (re - rt + blend * (1 / math.cos(reference_angle) - 1))
        / math.tan(reference_angle)
    )
    xn, rn = blend * math.sin(tn), rt + blend * (1 - math.cos(tn))
    qx = (re - rn + math.tan(tn) * xn - math.tan(te) * length) / (
        math.tan(tn) - math.tan(te)
    )
    qr = rn + math.tan(tn) * (qx - xn)
    if not all(math.isfinite(v) for v in (length, xn, rn, qx, qr, re)) or not (
        0 < xn < qx < length and rt < rn < qr < re
    ):
        raise InvalidInputError(
            "These angles/length/blend do not form a monotonic tangent bell. Adjust explicit geometry inputs."
        )
    arc_count = max(3, point_count // 5)
    points = []
    for i in range(arc_count):
        theta = tn * i / (arc_count - 1)
        radius = rt + blend * (1 - math.cos(theta))
        points.append(
            ContourPoint(
                blend * math.sin(theta), radius, math.degrees(theta), (radius / rt) ** 2
            )
        )
    curve, derivatives = quadratic_bezier(
        ((xn, rn), (qx, qr), (length, re)), point_count - arc_count + 1
    )
    for p, d in zip(curve[1:], derivatives[1:], strict=True):
        points.append(
            ContourPoint(
                float(p[0]),
                float(p[1]),
                math.degrees(math.atan2(d[1], d[0])),
                float((p[1] / rt) ** 2),
            )
        )
    if any(b.x_m <= a.x_m or b.radius_m < a.radius_m for a, b in pairwise(points)):
        raise InvalidInputError("Contour is not monotonic.")
    return tuple(points)
