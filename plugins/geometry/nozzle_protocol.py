"""Separate bounded engine-nozzle slice; the fixed-fixture validator is unchanged."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

from plugins.geometry.protocol import IDENTITY
from systems.contracts.geometry import (
    DesignSnapshot,
    GeometryBuildRequest,
    GeometryFeatureGraph,
    Representation,
)
from systems.contracts.geometry._wire import require

VERSION = "occt-7.8.1.ocp-7.8.1.1.r07nozzle.v1"
POLICY = "r07.engine-nozzle-software-qa.v1"


@dataclass(frozen=True)
class NozzleProfile:
    points: tuple[tuple[float, float], ...]
    radial_thickness_m: float


def profile(snapshot: DesignSnapshot, graph: GeometryFeatureGraph) -> NozzleProfile:
    graph.validate_snapshot(snapshot)
    require(snapshot.project_id.startswith("engine-design-"), "SOURCE_NAMESPACE", "Engine nozzle policy requires the explicit engine-design namespace; fixtures cannot enter it")
    require(len(snapshot.frames) == 1 and snapshot.frames[0].parent_frame_id is None
            and snapshot.frames[0].origin_m == (0., 0., 0.) and snapshot.frames[0].rotation == IDENTITY
            and snapshot.frame_id == "throat-x", "UNSUPPORTED_FRAME", "Nozzle V1 requires the explicit throat +X identity frame")
    by_id = {f.feature_id: f for f in graph.features}
    require(set(by_id) == {"inner-profile", "wall-profile", "nozzle-wall"} and graph.output_feature_ids == ("nozzle-wall",), "UNSUPPORTED_GRAPH", "Exact qualified profile/wall/revolve DAG required")
    expected = {
        "inner-profile": ("polyline_profile_intent", ()),
        "wall-profile": ("radial_offset_closed_profile_intent", ("inner-profile",)),
        "nozzle-wall": ("revolve_x_intent", ("wall-profile",)),
    }
    for name, feature in by_id.items():
        require((feature.operation, feature.dependency_ids) == expected[name]
                and feature.frame_id == snapshot.frame_id and feature.representation is Representation.ANALYTIC_BREP,
                "UNSUPPORTED_GRAPH", "Nozzle feature operation/dependencies/frame/representation differ")
    refs = set(by_id["inner-profile"].parameter_refs)
    require(len(refs) % 2 == 0 and 4 <= len(refs) <= 258, "CAPACITY_LIMIT", "Native nozzle profile requires 2–129 retained stations")
    count = len(refs) // 2
    names = {f"station-{i}-{key}" for i in range(count) for key in ("x", "radius")}
    values = {p.name: p for p in snapshot.parameters_si}
    require(refs == names and set(values) == names | {"radial-wall-thickness", "source-tolerance", "export-tolerance"}
            and by_id["wall-profile"].parameter_refs == ("radial-wall-thickness",) and not by_id["nozzle-wall"].parameter_refs,
            "PARAMETER_BINDING", "Exact feature-qualified station/wall/tolerance bindings required")
    require(all(p.unit_symbol == "m" and p.dimension == (1, 0, 0, 0, 0, 0, 0) for p in values.values()), "INVALID_UNIT", "Nozzle geometry requires SI metres")
    points = tuple((values[f"station-{i}-x"].value_si, values[f"station-{i}-radius"].value_si) for i in range(count))
    thickness = values["radial-wall-thickness"].value_si
    require(points[0][0] == 0 and 1e-6 <= thickness <= .1 and points[-1][0] <= 3
            and all(1e-5 <= r < 1 and r + thickness <= 1 for _, r in points)
            and all(b[0] - a[0] > 1e-9 and b[1] > a[1] for a, b in pairwise(points)),
            "GEOMETRY_ENVELOPE", "Nozzle requires a strictly divergent retained profile in the declared local size/edge/thickness envelope; no repair")
    return NozzleProfile(points, thickness)


def validate(request: GeometryBuildRequest, snapshot: DesignSnapshot, graph: GeometryFeatureGraph) -> NozzleProfile:
    result = profile(snapshot, graph)
    parameters = {p.name: p.value_si for p in snapshot.parameters_si}
    require(request.snapshot_id == snapshot.snapshot_id and request.feature_graph_id == graph.graph_id
            and request.feature_graph_sha256 == graph.content_sha256, "STALE_REQUEST", "Nozzle request must bind the exact snapshot and graph")
    require(request.backend_id == "occt" and request.backend_version == VERSION and request.representation is Representation.ANALYTIC_BREP
            and request.approximation_profile == "none" and request.voxel_resolution_m is None
            and request.frame_id == snapshot.frame_id and {f.value for f in request.output_formats} == {"step", "stl"},
            "UNSUPPORTED_BUILD", "Nozzle V1 requires pinned OCCT, analytic sampled-profile source and both independent STEP/STL candidate exports")
    require(request.source_tolerance_m == parameters["source-tolerance"] and request.export_tolerance_m == parameters["export-tolerance"]
            and request.source_tolerance_m >= 1e-10 and request.export_tolerance_m >= 1e-7
            and max(request.source_tolerance_m, request.export_tolerance_m) < result.radial_thickness_m / 2,
            "UNSUPPORTED_TOLERANCE", "Exact retained source/export tolerances must meet declared kernel/float32 floors and radial-wall separation")
    return result
