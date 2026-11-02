"""Observe bounded contract costs on this host; not a geometry/performance gate."""
import json
import statistics
import time
import tracemalloc
from dataclasses import replace
from pathlib import Path

from systems.contracts.geometry import CoordinateFrame, GeometryFeature, GeometryFeatureGraph, Representation
from tests.fixtures.geometry_contracts import IDENTITY, snapshot

HERE = Path(__file__).resolve().parent


def main():
    base = snapshot()
    frames = tuple(CoordinateFrame("world" if i == 0 else f"frame-{i}", None if i == 0 else ("world" if i == 1 else f"frame-{i-1}"),
                                   (0, 0, i * 1e-4), IDENTITY) for i in range(64))
    parameters = tuple(replace(base.parameters_si[0], name=f"parameter-{i}", value_si=i / 1000) for i in range(256))
    value = replace(base, parameters_si=parameters, frames=frames, frame_id="frame-63")
    features = tuple(GeometryFeature(f"feature-{i:03}", "fixture.intent", (f"parameter-{i % 256}",),
                                     () if i == 0 else (f"feature-{i-1:03}",), "frame-63", Representation.ANALYTIC_BREP) for i in range(512))
    graph = GeometryFeatureGraph("bounded-fixture", value.snapshot_id, features, ("feature-511",))
    graph.validate_snapshot(value)
    replacement = replace(value, revision_id="r2", parameters_si=(replace(parameters[0], value_si=.125), *parameters[1:]))
    timings = []
    graph_json, snapshot_json = graph.to_json(), value.to_json()
    tracemalloc.start()
    for _ in range(5):
        start = time.perf_counter()
        assert GeometryFeatureGraph.from_json(graph_json) == graph
        assert type(value).from_json(snapshot_json) == value
        assert len(graph.fingerprints(value)) == 512
        impact = graph.impact(value, replacement)
        assert len(impact.stale_features) == 512
        timings.append((time.perf_counter() - start) * 1000)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result = {"synthetic_only": True, "native_kernel_invoked": False, "timing_gate_claimed": False,
              "workload": "snapshot+graph decode, full fingerprints and transitive impact; tracemalloc enabled",
              "feature_count": 512, "parameter_count": 256, "frame_count": 64, "iterations": 5,
              "snapshot_json_bytes": len(snapshot_json.encode()), "graph_json_bytes": len(graph_json.encode()),
              "median_ms": statistics.median(timings), "max_ms": max(timings), "samples_ms": timings, "peak_tracemalloc_bytes": peak}
    (HERE / "contract_costs.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("feature_count", "median_ms", "peak_tracemalloc_bytes", "timing_gate_claimed")}))


if __name__ == "__main__":
    main()
