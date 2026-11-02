"""Predeclared analytic references/policies for synthetic P07 software fixtures only."""
from __future__ import annotations

import hashlib
from pathlib import Path

from core.quantity import Quantity
from core.unit import SI
from plugins.geometry.protocol import CAD_VERSION, PICO_VERSION
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

STAMP = "2026-10-09T00:00:00+00:00"
IDENTITY = (1, 0, 0, 0, 1, 0, 0, 0, 1)
OPERATIONS = ("sphere", "union", "difference", "intersection", "self_union", "self_difference", "disjoint_intersection")


def case(operation="sphere", backend="picogk", voxel=.0005, formats=None):
    representation = Representation.IMPLICIT_FIELD if backend == "picogk" else Representation.ANALYTIC_BREP
    source = SourceReference("p07-analytic-fixture", "tests/fixtures/ngg_cases.py", hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    radius = .01
    definitions = []
    features = []
    def primitive(name, kind, x):
        params = {"radius": radius, "x": x, "y": 0., "z": 0.}
        if kind == "cylinder":
            params["height"] = .02
        elif kind == "box":
            params = {"width": .02, "depth": .03, "height": .04, "x": x, "y": 0., "z": 0.}
        definitions.extend(SIParameter.from_quantity(name + "." + key, Quantity(value, SI.get("m")), si_unit="m", source_ref_id=source.ref_id) for key, value in params.items())
        features.append(GeometryFeature(name, "primitive." + kind, tuple(name + "." + k for k in params), (), "world", representation))
    if operation in {"sphere", "cylinder", "box"}:
        primitive("body", operation, 0)
        output = "body"
    else:
        primitive("pair.lhs", "sphere", 0)
        primitive("pair.rhs", "sphere", 0 if operation.startswith("self_") else (.03 if operation == "disjoint_intersection" else .01))
        op = operation.removeprefix("self_").removeprefix("disjoint_")
        features.append(GeometryFeature("result", "boolean." + op, (), ("pair.lhs", "pair.rhs"), "world", representation))
        output = "result"
    snapshot = DesignSnapshot("p07-software-fixtures", "r1-" + operation, tuple(definitions),
                              (CoordinateFrame("world", None, (0, 0, 0), IDENTITY),), "world", (source,), STAMP)
    graph = GeometryFeatureGraph("fixture-" + operation, snapshot.snapshot_id, tuple(features), (output,))
    request = GeometryBuildRequest("request-" + operation, snapshot.snapshot_id, graph.graph_id, graph.content_sha256,
                                   backend, PICO_VERSION if backend == "picogk" else CAD_VERSION, representation,
                                   "sparse_volume" if backend == "picogk" else "none", 1.5 * voxel if backend == "picogk" else 1e-8,
                                   1.5 * voxel if backend == "picogk" else 1e-6, voxel if backend == "picogk" else None,
                                   formats if formats is not None else ((OutputFormat.STL,) if backend == "picogk" else (OutputFormat.STEP,)),
                                   "world", "correlation-" + operation)
    return snapshot, graph, request
