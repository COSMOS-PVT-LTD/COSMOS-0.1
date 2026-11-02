"""Independent closed-form surface references for bounded manufactured cases.

No kernel queries, mesh-derived areas or engine acceptance tolerances. These
formulas assume the fixture's disjoint, source-validated bores/cavities and
planar connected openings; they are NOT a general CSG surface-area algorithm.
"""

import math
from copy import deepcopy
from itertools import pairwise

import numpy as np

from systems.geometry.component_model import compile_model
from systems.geometry.component_reference import PartReference
from systems.geometry.qualification_policy import validate
from tests.fixtures.component_geometry import model
from tests.fixtures.geometry_qualification import pipe_policy

FAMILIES = (
    "profile.wall",
    "profile.solid",
    "cooling.axial_sector",
    "injector.showerhead",
    "injector.doublet",
    "injector.biprop_doublet",
    "injector.biprop_radial_doublet",
    "injector.triplet",
    "injector.coaxial",
    "injector.pintle",
    "manifold.dual_annular",
    "manifold.cooling_annular",
    "manifold.cooling_front_supply",
    "interface.bolted_flange",
    "interface.bolt_pattern",
    "interface.face_groove",
    "bolted-injector",
    "grooved-bolted-injector",
    "five-grooved-bolted-injector",
    "pipe.circular",
    "pipe.elbow",
    "placement.rigid",
)
SPACINGS = (0.0003125, 0.00025, 0.0002)
PINTLE_SPACINGS = (0.000125, 0.0001, 0.00008)


def family_plan(kind):
    spec = model(
        "pipe.circular"
        if kind == "placement.rigid"
        else "profile.wall"
        if kind == "profile.solid"
        else kind
    )
    if kind == "profile.solid":
        spec["features"][0]["operation"] = kind
        for key, value in spec["features"][0]["parameters"].items():
            if key.startswith("inner"):
                value["value"] = 0.0
    if kind == "placement.rigid":
        spec["frames"].append(
            {
                "id": "placed",
                "parent": "world",
                "origin": [{"value": v, "unit": "m"} for v in (0.03, -0.02, 0.01)],
                "rotation": [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            }
        )
        spec["features"].append(
            {
                "id": "placed",
                "operation": kind,
                "frame": "placed",
                "depends_on": ["body"],
                "parameters": {},
            }
        )
        spec["outputs"] = ["placed"]
    return compile_model(
        spec,
        "engine-component-r08-manufactured-" + kind,
        "software-fixture",
        "2026-10-25T00:00:00Z",
    )


def end_area(row, width):
    _, ri, ro = row
    return width * (ro * ro - ri * ri) / 2


def surface(profile, sector=None):
    width = 2 * math.pi if sector is None else sector[1]
    sides = sum(
        width
        * (
            (a[2] + b[2]) * math.hypot(b[0] - a[0], b[2] - a[2])
            + (a[1] + b[1]) * math.hypot(b[0] - a[0], b[1] - a[1])
        )
        / 2
        for a, b in pairwise(profile)
    )
    if sector is not None:
        # Two plane meridian faces; trapezoidal integration is exact here.
        sides += sum(
            (b[0] - a[0]) * (a[2] - a[1] + b[2] - b[1]) for a, b in pairwise(profile)
        )
    return sides + end_area(profile[0], width) + end_area(profile[-1], width)


def area_reference(part):
    if part.pipe and part.pipe.bend_radius is not None:
        p = part.pipe
        return 2 * math.pi * (
            p.outer_radius + p.bore_radius
        ) * p.bend_radius * p.angle_rad + 2 * math.pi * (
            p.outer_radius**2 - p.bore_radius**2
        )
    area = surface(part.profile, part.sector)
    for hole in part.holes:
        a, b = hole.axial_range or (part.profile[0][0], part.profile[-1][0])
        tilt = math.sqrt(1 + sum(s * s for s in hole.slope_yz))
        area += 2 * math.pi * hole.radius * tilt * ((b - a) - hole.radius)
    for cavity in part.cavities:
        width = 2 * math.pi if cavity.sector is None else cavity.sector[1]
        area += surface(cavity.profile, cavity.sector)
        if cavity.open_face:
            row = cavity.profile[0 if cavity.open_face == "start" else -1]
            area -= 2 * end_area(row, width)
        elif cavity.open_passage:
            # Sector connects the annular plenum and external front face.
            area -= 2 * (
                end_area(cavity.profile[0], width) + end_area(cavity.profile[-1], width)
            )
    if part.cooling:
        c = part.cooling
        channel = tuple(
            (x, ri + c.hot_ligament, ri + c.hot_ligament + c.depth)
            for x, ri, _ in part.profile
        )
        area += c.count * (
            surface(channel, (0.0, c.width_rad))
            - 2
            * (end_area(channel[0], c.width_rad) + end_area(channel[-1], c.width_rad))
        )
    return area


def critical_witnesses(plan, part):
    ref = PartReference(plan, part)
    rotation, translation = plan.placement(part.frame_id)
    probes = []

    def add(label, kind, points):
        world = np.array(points) @ rotation.T + translation
        if not (np.abs(ref.sdf(world)) <= 1e-6).all():
            return False
        span = float(np.linalg.norm(world[1] - world[0]))
        probes.append(
            {
                "id": label,
                "kind": kind,
                "points_m": world.tolist(),
                "minimum_m": span * 0.5,
                "maximum_m": span * 1.5,
                "surface_tolerance_m": 0.00045,
                "source": "Independent source-coordinate fixture witnesses; local sampled span, not global minimum",
            }
        )
        return True

    if part.pipe and part.pipe.bend_radius is not None:
        p = part.pipe
        angle = p.angle_rad / 2
        x, y = p.bend_radius * math.sin(angle), p.bend_radius * (1 - math.cos(angle))
        assert add(
            "bend-wall", "WALL_SPAN", [(x, y, p.bore_radius), (x, y, p.outer_radius)]
        )
    else:
        a, b = part.profile[:2]
        x, ri, ro = (np.array(a) + np.array(b)) / 2
        if part.cooling:
            ro = ri + part.cooling.hot_ligament
        angles = (
            [part.sector[0] + part.sector[1] / 2]
            if part.sector
            else np.arange(64) * 2 * math.pi / 64
        )
        for angle in angles:
            radii = (ri, ro) if ri else (-ro, ro)
            if add(
                "wall-or-diameter",
                "WALL_SPAN" if ri else "DIMENSION",
                [(x, r * math.cos(angle), r * math.sin(angle)) for r in radii],
            ):
                break
        else:
            raise AssertionError("No valid source wall witness for " + part.part_id)
    for index, hole in enumerate(part.holes):
        a, b = hole.axial_range or (part.profile[0][0], part.profile[-1][0])
        x = (a + b) / 2
        slope = np.array(hole.slope_yz)
        transverse = (
            np.array([-slope[1], slope[0]])
            if np.linalg.norm(slope)
            else np.array([1.0, 0.0])
        )
        transverse /= np.linalg.norm(transverse)
        center = np.array(hole.center_yz) + x * slope
        assert add(
            "port-" + str(index),
            "PORT_DIAMETER",
            [np.r_[x, center + sign * hole.radius * transverse] for sign in (-1, 1)],
        )
    for index, cavity in enumerate(part.cavities):
        x, ri, ro = (np.array(cavity.profile[0]) + np.array(cavity.profile[-1])) / 2
        angle = cavity.sector[0] + cavity.sector[1] / 2 if cavity.sector else 0.7
        assert add(
            "cavity-" + str(index),
            "INTERFACE_SPAN" if cavity.open_face else "CHANNEL_SPAN",
            [(x, r * math.cos(angle), r * math.sin(angle)) for r in (ri, ro)],
        )
    if part.part_id.endswith(".rod-deflector"):
        x, _, radius = part.profile[-1]
        assert add(
            "deflector-rim-diameter", "DIMENSION", [(x, -radius, 0.0), (x, radius, 0.0)]
        )
        probes[-1].update(minimum_m=2 * radius - 0.0005, maximum_m=2 * radius + 0.0005)
    return probes


def family_policy(plan):
    policy = deepcopy(pipe_policy())
    policy["reference_source"] = (
        "Independent frustum/sector/torus/elliptic-opening formulas in tests/fixtures/geometry_qualification_families.py; manufactured software cases only"
    )
    # A separate explicit study, not automatic refinement of a failed attempt.
    # Original coarse failures are retained in the development campaign report.
    spacings = (
        PINTLE_SPACINGS
        if any(f.operation == "injector.pintle" for f in plan.graph.features)
        else SPACINGS
    )
    policy["refinement_resolutions_m"] = list(spacings)
    policy["parts"] = []
    policy["regions"] = []
    policy["boundaries"] = []
    for part in plan.parts:
        limits = deepcopy(pipe_policy()["parts"][0])
        limits.update(
            part_id=part.part_id,
            relative_volume=0.05,
            relative_area=0.08,
            reference_area_m2=area_reference(part),
            area_reference_source=policy["reference_source"],
            critical_features=critical_witnesses(plan, part),
        )
        policy["parts"].append(limits)
        policy["regions"].append(
            {
                "part_id": part.part_id,
                "role": part.role,
                "material": "Synthetic region, no material properties",
                "source": "Manufactured software fixture only",
            }
        )
        policy["boundaries"].append(
            {
                "part_id": part.part_id,
                "semantic_id": part.part_id + ":all",
                "scope": "WHOLE_PART",
                "purpose": "Software QA only",
                "source": "Exact fixture part identity",
            }
        )
    minimum = min(
        c["minimum_m"] for p in policy["parts"] for c in p["critical_features"]
    )
    policy["mesh_intent"]["minimum_feature_m"] = min(minimum, 0.0002)
    policy["mesh_intent"]["maximum_edge_m"] = min(minimum, 0.0002) / 4
    return validate(policy, plan)
