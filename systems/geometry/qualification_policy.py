"""Explicit intended-use contracts. No universal engineering tolerances/defaults."""

from __future__ import annotations

import math

import numpy as np

from simulation.component_handoff import ComponentMeshConstraints
from systems.contracts.geometry._wire import require
from systems.geometry.component_reference import PartReference

SCHEMA = "cosmos.geometry-qualification-policy.v1"
USES = {"SOFTWARE_QUALIFICATION", "GEOMETRY_ANALYSIS_PREPARATION"}


def exact(value, keys, label):
    require(
        type(value) is dict and set(value) == set(keys),
        "R08_FIELDS",
        "Exact " + label + " fields required",
    )


def text(value, label, maximum=2048):
    require(
        type(value) is str and 0 < len(value.strip()) <= maximum,
        "R08_TEXT",
        "Explicit bounded " + label + " required",
    )
    return value


def number(value, label, *, low=0.0, high=10.0, zero=False):
    require(
        type(value) in (int, float)
        and math.isfinite(value)
        and (low <= value if zero else low < value)
        and value <= high,
        "R08_NUMBER",
        "Explicit finite SI " + label + " outside supported bounds",
    )
    return float(value)


def vector(value):
    require(
        type(value) is list
        and len(value) == 3
        and all(
            type(v) in (int, float) and math.isfinite(v) and abs(v) <= 10 for v in value
        ),
        "R08_POINT",
        "Three explicit finite world-coordinate metre values required",
    )
    return np.array(value, dtype=float)


def validate(value, plan):
    exact(
        value,
        {
            "schema",
            "unit_system",
            "intended_use",
            "applicability",
            "reference_source",
            "sampling",
            "parts",
            "regions",
            "boundaries",
            "mesh_intent",
            "refinement_resolutions_m",
            "require_cross_representation",
            "require_certified_self_intersection",
        },
        "predeclared policy",
    )
    require(
        value["schema"] == SCHEMA
        and value["unit_system"] == "SI_m"
        and type(value["intended_use"]) is str
        and value["intended_use"] in USES,
        "R08_SCOPE",
        "Only explicit SI software/geometry-analysis preparation policies; no manufacturing/physical approval",
    )
    for key in ("applicability", "reference_source"):
        text(value[key], key)
    for key in ("require_cross_representation", "require_certified_self_intersection"):
        require(
            type(value[key]) is bool,
            "R08_POLICY",
            "Explicit Boolean requirements required",
        )
    exact(value["sampling"], {"samples_per_part", "outlier_limit"}, "sampling")
    for key, low, high in (("samples_per_part", 16, 2048), ("outlier_limit", 1, 64)):
        n = value["sampling"][key]
        require(
            type(n) is int and low <= n <= high,
            "R08_SAMPLING",
            "Explicit bounded sampling/outlier counts required",
        )
    resolutions = value["refinement_resolutions_m"]
    require(
        type(resolutions) is list and len(resolutions) in {0, 3},
        "R08_REFINEMENT",
        "Zero (analytic-only) or three predeclared implicit resolutions required",
    )
    for n in resolutions:
        number(n, "voxel resolution", low=2.499999e-5, high=0.002)
    require(
        not resolutions or resolutions[0] > resolutions[1] > resolutions[2],
        "R08_REFINEMENT",
        "Three distinct decreasing voxel spacings required; no automatic refinement",
    )
    require(
        not value["require_cross_representation"] or len(resolutions) == 3,
        "R08_REFINEMENT",
        "Cross-representation qualification requires the explicit three-resolution study",
    )
    parts = {p.part_id: p for p in plan.parts}
    require(
        type(value["parts"]) is list
        and len(value["parts"]) == len(parts)
        and all(
            type(p) is dict and type(p.get("part_id")) is str for p in value["parts"]
        )
        and {p["part_id"] for p in value["parts"]} == set(parts),
        "R08_PARTS",
        "One explicit policy per exact source part; no omissions/duplicates/extra bodies",
    )
    source_tolerance = next(
        p.value_si for p in plan.snapshot.parameters_si if p.name == "source_tolerance"
    )
    critical_count = 0
    minima = []
    for policy in value["parts"]:
        exact(
            policy,
            {
                "part_id",
                "relative_volume",
                "relative_area",
                "reference_area_m2",
                "area_reference_source",
                "centroid_m",
                "bounds_m",
                "reference_residual_m",
                "reverse_distance_m",
                "representation_distance_m",
                "critical_features",
            },
            "per-part policy",
        )
        for name in ("relative_volume", "relative_area"):
            number(policy[name], name, high=0.1)
        number(policy["reference_area_m2"], "reference area [m2]", high=1000)
        text(policy["area_reference_source"], "independent area reference/source")
        for name in (
            "centroid_m",
            "bounds_m",
            "reference_residual_m",
            "reverse_distance_m",
            "representation_distance_m",
        ):
            number(policy[name], name, high=0.1)
        probes = policy["critical_features"]
        require(
            type(probes) is list and 1 <= len(probes) <= 32,
            "R08_CRITICAL",
            "Every part needs explicit local critical-feature witness coverage",
        )
        ref = PartReference(plan, parts[policy["part_id"]])
        ids = set()
        for probe in probes:
            exact(
                probe,
                {
                    "id",
                    "kind",
                    "points_m",
                    "minimum_m",
                    "maximum_m",
                    "surface_tolerance_m",
                    "source",
                },
                "critical witness",
            )
            text(probe["id"], "critical feature ID", 128)
            require(
                probe["id"] not in ids
                and type(probe["kind"]) is str
                and probe["kind"]
                in {
                    "WALL_SPAN",
                    "CHANNEL_SPAN",
                    "PORT_DIAMETER",
                    "INTERFACE_SPAN",
                    "DIMENSION",
                },
                "R08_CRITICAL",
                "Unique labelled critical feature/kind required",
            )
            ids.add(probe["id"])
            text(probe["source"], "critical witness reference/applicability")
            number(probe["minimum_m"], "minimum critical span", high=10)
            number(probe["maximum_m"], "maximum critical span", high=10)
            number(probe["surface_tolerance_m"], "critical surface tolerance", high=0.1)
            require(
                type(probe["points_m"]) is list and len(probe["points_m"]) == 2,
                "R08_CRITICAL",
                "Two source-bound surface witnesses required",
            )
            points = np.array([vector(p) for p in probe["points_m"]])
            span = float(np.linalg.norm(points[1] - points[0]))
            require(
                probe["minimum_m"] <= span <= probe["maximum_m"]
                and span > 0
                and bool((np.abs(ref.sdf(points)) <= source_tolerance).all()),
                "R08_CRITICAL_SOURCE",
                "Critical witnesses must lie on this exact analytic source and bound its nominal span",
            )
            minima.append(probe["minimum_m"])
        critical_count += len(probes)
    require(
        critical_count <= 256,
        "R08_CAPACITY",
        "At most 256 explicit critical witnesses per policy",
    )
    regions = value["regions"]
    require(
        type(regions) is list and len(regions) == len(parts),
        "R08_REGIONS",
        "Every exact part requires a material/fluid region",
    )
    seen = set()
    for region in regions:
        exact(region, {"part_id", "role", "material", "source"}, "region")
        require(
            type(region["part_id"]) is str
            and region["part_id"] in parts
            and region["part_id"] not in seen
            and region["role"] == parts[region["part_id"]].role,
            "R08_REGIONS",
            "Unique source-bound material/fluid regions required",
        )
        seen.add(region["part_id"])
        text(region["material"], "material label", 240)
        text(region["source"], "material applicability/source")
    boundaries = value["boundaries"]
    require(
        type(boundaries) is list and 1 <= len(boundaries) <= 256,
        "R08_SELECTION",
        "Explicit bounded named handoff selections required",
    )
    seen = set()
    for boundary in boundaries:
        exact(
            boundary,
            {"semantic_id", "part_id", "scope", "purpose", "source"},
            "named boundary",
        )
        text(boundary["semantic_id"], "semantic ID", 256)
        require(
            boundary["semantic_id"] not in seen
            and type(boundary["part_id"]) is str
            and boundary["part_id"] in parts
            and type(boundary["scope"]) is str
            and boundary["scope"] in {"WHOLE_PART", "ANALYTIC_FACE"},
            "R08_SELECTION",
            "Unique explicit part/analytic-face selection required",
        )
        seen.add(boundary["semantic_id"])
        for key in ("purpose", "source"):
            text(boundary[key], key)
    exact(
        value["mesh_intent"],
        {
            "maximum_edge_m",
            "minimum_feature_m",
            "cells_across_feature",
            "curvature_tolerance_m",
            "maximum_cells",
            "source",
        },
        "mesh intent",
    )
    mesh = ComponentMeshConstraints(**value["mesh_intent"])
    require(
        mesh.minimum_feature_m <= min(minima),
        "R08_MESH",
        "Mesh intent must resolve the smallest declared critical span; no inferred/generated volume mesh",
    )
    return value
