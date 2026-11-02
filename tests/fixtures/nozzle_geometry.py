"""Manufactured geometry/software QA cases; never owner design defaults."""

from core.quantity import Quantity
from core.unit import SI
from plugins.geometry.nozzle_protocol import VERSION
from systems.contracts.geometry import (
    CoordinateFrame,
    DesignSnapshot,
    GeometryBuildRequest,
    GeometryFeature,
    GeometryFeatureGraph,
    OutputFormat,
    Representation,
    SIParameter,
    SourceReference,
)


def case(points=((0., .01), (.04, .02)), thickness=.002, *, tolerance=1e-5):
    parameters = [SIParameter.from_quantity(f"station-{i}-{key}", Quantity(v, SI.get("m")), si_unit="m", source_ref_id="synthetic") for i, row in enumerate(points) for key, v in zip(("x", "radius"), row, strict=True)]
    parameters.extend(SIParameter.from_quantity(name, Quantity(value, SI.get("m")), si_unit="m", source_ref_id="synthetic") for name, value in (("radial-wall-thickness", thickness), ("source-tolerance", 1e-6), ("export-tolerance", tolerance)))
    snapshot = DesignSnapshot("engine-design-synthetic-software-only", "manufactured-nozzle", tuple(parameters), (CoordinateFrame("throat-x", None, (0., 0., 0.), (1., 0., 0., 0., 1., 0., 0., 0., 1.)),), "throat-x", (SourceReference("synthetic", "tests/fixtures/nozzle_geometry.py", "1" * 64),), "2026-10-20T00:00:00+00:00")
    graph = GeometryFeatureGraph("manufactured-nozzle-graph", snapshot.snapshot_id, (
        GeometryFeature("inner-profile", "polyline_profile_intent", tuple(p.name for p in parameters if p.name.startswith("station-")), (), "throat-x", Representation.ANALYTIC_BREP),
        GeometryFeature("wall-profile", "radial_offset_closed_profile_intent", ("radial-wall-thickness",), ("inner-profile",), "throat-x", Representation.ANALYTIC_BREP),
        GeometryFeature("nozzle-wall", "revolve_x_intent", (), ("wall-profile",), "throat-x", Representation.ANALYTIC_BREP),
    ), ("nozzle-wall",))
    request = GeometryBuildRequest("r07-software-request", snapshot.snapshot_id, graph.graph_id, graph.content_sha256, "occt", VERSION, Representation.ANALYTIC_BREP, "none", 1e-6, tolerance, None, (OutputFormat.STEP, OutputFormat.STL), "throat-x", "r07-software-correlation")
    return snapshot, graph, request


def qa_spec():
    return {"relative_volume": {"value": .005, "unit": "1"}, "centroid": {"value": 2e-5, "unit": "m"}, "surface_distance": {"value": 2e-5, "unit": "m"}, "source": "Predeclared synthetic software-reference QA ceilings only; not manufacturing tolerances or hardware acceptance"}
