"""NGG worker transport carries exact P06 wire text, not re-rounded native JSON."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from systems.contracts.geometry import (
    DesignSnapshot,
    GeometryBuildRequest,
    GeometryFeatureGraph,
)
from systems.contracts.geometry._wire import MAX_WIRE_BYTES, identifier, require, sha

PROTOCOL = "cosmos.ngg.worker.v1"
PICO_VERSION = "picogk-2.2.0.p07v1"
CAD_VERSION = "occt-7.8.1.ocp-7.8.1.1.p07v1"
IDENTITY = (1., 0., 0., 0., 1., 0., 0., 0., 1.)


def payload(job_id: str, request: GeometryBuildRequest, snapshot: DesignSnapshot, graph: GeometryFeatureGraph,
            *, action: str = "build") -> bytes:
    identifier(job_id, "job_id")
    require(action in {"build", "health"}, "UNSUPPORTED_OPERATION", "Unsupported worker action")
    graph.validate_snapshot(snapshot)
    require(request.snapshot_id == snapshot.snapshot_id and request.feature_graph_sha256 == graph.content_sha256
            and request.feature_graph_id == graph.graph_id, "STALE_REQUEST", "Worker request has stale lineage")
    wires = {"request": request.to_json(), "snapshot": snapshot.to_json(), "graph": graph.to_json()}
    value = {"protocol": PROTOCOL, "action": action, "job_id": job_id, "correlation_id": request.correlation_id,
             "wires": wires, "wire_sha256": {name: hashlib.sha256(text.encode()).hexdigest() for name, text in wires.items()}}
    result = json.dumps(value, separators=(",", ":"), allow_nan=False).encode()
    require(len(result) <= MAX_WIRE_BYTES, "CONTRACT_LIMIT", "Worker envelope exceeds byte limit")
    return result


def parse_request(raw: bytes) -> tuple[str, str, GeometryBuildRequest, DesignSnapshot, GeometryFeatureGraph]:
    require(len(raw) <= MAX_WIRE_BYTES, "CONTRACT_LIMIT", "Worker request exceeds byte limit")
    def pairs(items):
        require(len({k for k, _ in items}) == len(items), "DUPLICATE_KEY", "Duplicate protocol key")
        return dict(items)
    value = json.loads(raw, object_pairs_hook=pairs)
    require(type(value) is dict and set(value) == {"protocol", "action", "job_id", "correlation_id", "wires", "wire_sha256"}, "INVALID_FIELDS", "Unknown/missing protocol fields")
    require(value["protocol"] == PROTOCOL and value["action"] in {"build", "health"}, "PROTOCOL_VERSION", "Unsupported worker protocol/action")
    identifier(value["job_id"], "job_id")
    identifier(value["correlation_id"], "correlation_id")
    require(type(value["wires"]) is dict and type(value["wire_sha256"]) is dict
            and set(value["wires"]) == set(value["wire_sha256"]) == {"request", "snapshot", "graph"}, "INVALID_FIELDS", "Invalid wire envelope")
    for name, text in value["wires"].items():
        require(type(text) is str and type(value["wire_sha256"][name]) is str, "INVALID_TYPE", "Expected exact wire strings/hashes")
        require(hashlib.sha256(text.encode()).hexdigest() == value["wire_sha256"][name], "HASH_MISMATCH", "Wire bytes changed at worker boundary")
    request = GeometryBuildRequest.from_json(value["wires"]["request"])
    snapshot = DesignSnapshot.from_json(value["wires"]["snapshot"])
    graph = GeometryFeatureGraph.from_json(value["wires"]["graph"])
    graph.validate_snapshot(snapshot)
    require(request.correlation_id == value["correlation_id"] and request.snapshot_id == snapshot.snapshot_id
            and request.feature_graph_sha256 == graph.content_sha256 and request.feature_graph_id == graph.graph_id,
            "STALE_REQUEST", "Request lineage/correlation mismatch")
    return value["job_id"], value["action"], request, snapshot, graph


def validate_slice(request: GeometryBuildRequest, snapshot: DesignSnapshot, graph: GeometryFeatureGraph, backend: str) -> None:
    require(request.backend_id == backend, "BACKEND_MISMATCH", "Requested backend does not match configured worker")
    require(request.backend_version == (PICO_VERSION if backend == "picogk" else CAD_VERSION), "BACKEND_VERSION", "Unqualified backend version")
    require(len(graph.features) <= 64 and len(graph.output_feature_ids) == 1, "UNSUPPORTED_OPERATION", "V1 workers support up to 64 features and one output")
    require(len(snapshot.frames) == 1 and snapshot.frames[0].parent_frame_id is None
            and snapshot.frames[0].origin_m == (0., 0., 0.) and snapshot.frames[0].rotation == IDENTITY,
            "UNSUPPORTED_FRAME", "V1 backend slice requires an explicit identity root frame")
    require(all(f.frame_id == request.frame_id == snapshot.frame_id for f in graph.features), "UNSUPPORTED_FRAME", "Unsupported feature frame")
    parameters = {p.name: p for p in snapshot.parameters_si}
    if backend == "picogk":
        h = request.voxel_resolution_m
        require(h is not None and .00025 <= h <= .002, "RESOLUTION", "Outside bounded PicoGK resolution")
        assert h is not None
        radii = [parameters[f.feature_id + ".radius"].value_si for f in graph.features if f.operation == "primitive.sphere" and f.feature_id + ".radius" in parameters]
        require(all(4 <= r/h <= 160 for r in radii) and sum(8*(r/h)**3 for r in radii) <= 16_000_000, "CAPACITY_LIMIT", "Requested graph exceeds explicit local native work bound")
    supported = {"primitive.sphere", "boolean.union", "boolean.difference", "boolean.intersection"}
    if backend == "occt":
        supported |= {"primitive.box", "primitive.cylinder"}
    for feature in graph.features:
        require(feature.operation in supported, "UNSUPPORTED_OPERATION", "Backend does not support the requested feature", feature.operation)
        primitive = feature.operation.startswith("primitive.")
        require((primitive and not feature.dependency_ids) or (not primitive and len(feature.dependency_ids) == 2 and not feature.parameter_refs), "INVALID_FEATURE", "Invalid primitive/Boolean bindings")
        if feature.operation == "boolean.difference":
            require({d.rsplit(".", 1)[-1] for d in feature.dependency_ids} == {"lhs", "rhs"}, "INVALID_FEATURE", "Subtraction dependencies must explicitly encode .lhs/.rhs roles; canonical order is not an operand role")
        expected = {"primitive.sphere": {"radius", "x", "y", "z"}, "primitive.cylinder": {"radius", "height", "x", "y", "z"},
                    "primitive.box": {"width", "depth", "height", "x", "y", "z"}}.get(feature.operation, set())
        # Parameters are feature-qualified to avoid conflicting dimensions in a graph.
        names = {name.removeprefix(feature.feature_id + ".") for name in feature.parameter_refs}
        require(names == expected and all(name.startswith(feature.feature_id + ".") for name in feature.parameter_refs), "INVALID_FEATURE", "Primitive requires exact feature-qualified bindings")
        for name in feature.parameter_refs:
            parameter = parameters[name]
            require(parameter.unit_symbol == "m" and parameter.dimension == (1, 0, 0, 0, 0, 0, 0), "INVALID_UNIT", "Geometry dimensions must be SI metres", name)
            require(abs(parameter.value_si) <= .1 and (name.rsplit(".", 1)[-1] in {"x", "y", "z"} or parameter.value_si > 0), "DIMENSION_LIMIT", "Outside bounded local fixture slice", name)


@dataclass(frozen=True, slots=True)
class ExportFile:
    name: str
    sha256: str
    format: str
    file_unit: str


@dataclass(frozen=True, slots=True)
class BackendResult:
    source_name: str
    source_sha256: str
    exports: tuple[ExportFile, ...]
    metrics: dict[str, Any]  # Worker observations only, never trusted acceptance.


def checked_file(directory: Path, name: str, expected_sha: str, *, max_bytes: int = 64 * 1024**2) -> Path:
    require(type(name) is str and name in {"source.brep", "source.vdb", "export.step", "export.stl", "export-conditioned.stl"}, "UNSAFE_PATH", "Worker returned an unsupported filename")
    require(type(expected_sha) is str, "INVALID_HASH", "Expected a SHA256 string")
    sha(expected_sha, "artifact_sha256")
    path = directory / name
    require(not path.is_symlink() and path.is_file() and path.resolve().parent == directory.resolve(), "UNSAFE_PATH", "Worker artifact escaped the private job directory")
    require(0 < path.stat().st_size <= max_bytes, "ARTIFACT_LIMIT", "Worker artifact size is outside the explicit bound")
    require(hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha, "HASH_MISMATCH", "Worker artifact bytes do not match checksum")
    return path
