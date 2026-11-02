"""Isolated worker harness and independent NumPy binary-STL audit.

No PicoGK bindings are used in reimport, topology, or analytic reference calculations.
The only child commands are a fixed dotnet executable and the specified probe DLL.
"""
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SCHEMA = "cosmos.picogk.feasibility.v1"


def read_stl(path, strict_normals=True):
    data = Path(path).read_bytes()
    if len(data) < 84 or b"UNITS= m" not in data[:80]:
        raise ValueError("Missing explicit metre STL header or incomplete file")
    count = int.from_bytes(data[80:84], "little")
    if not count or len(data) != 84 + count * 50:
        raise ValueError("Invalid STL triangle count or byte length")
    dtype = np.dtype([("normal", "<f4", 3), ("vertices", "<f4", (3, 3)), ("attribute", "<u2")])
    records = np.frombuffer(data, dtype=dtype, offset=84)
    triangles = records["vertices"].astype(np.float64)
    normals = records["normal"].astype(np.float64)
    if not np.isfinite(triangles).all() or (strict_normals and not np.isfinite(normals).all()):
        raise ValueError("Nonfinite STL coordinates or normals")
    return triangles, normals


def audit_mesh(path, operation, radius, separation, voxel):
    tris, normals = read_stl(path, strict_normals=False)
    nonfinite_normals = int(np.count_nonzero(~np.isfinite(normals).all(axis=1)))
    vertices, inverse = np.unique(tris.reshape(-1, 3), axis=0, return_inverse=True)
    faces = inverse.reshape(-1, 3)
    cross = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    double_area = np.linalg.norm(cross, axis=1)
    degenerate = int(np.count_nonzero(double_area <= 1e-18))
    edges = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    unique_edges, edge_index, incidence = np.unique(np.sort(edges, axis=1), axis=0,
        return_inverse=True, return_counts=True)
    orientation = np.where(edges[:, 0] < edges[:, 1], 1, -1)
    edge_sum = np.bincount(edge_index, weights=orientation)
    nonmanifold = int(np.count_nonzero(incidence != 2))
    inconsistent = int(np.count_nonzero(edge_sum != 0))
    duplicate_faces = len(faces) - len(np.unique(np.sort(faces, axis=1), axis=0))
    signed_six_volume = np.einsum("ij,ij->i", tris[:, 0], np.cross(tris[:, 1], tris[:, 2]))
    signed_volume = float(signed_six_volume.sum() / 6)
    centroid = (signed_six_volume[:, None] * tris.sum(axis=1)).sum(axis=0) / (24 * signed_volume)
    volume = abs(signed_volume)
    sphere_volume = 4 * math.pi * radius**3 / 3
    overlap = math.pi * (4 * radius + separation) * (2 * radius - separation)**2 / 12
    expected_volume = {"sphere": sphere_volume, "self_union": sphere_volume,
        "union": 2 * sphere_volume - overlap, "difference": sphere_volume - overlap,
        "intersection": overlap}[operation]
    expected_x = {"sphere": 0, "self_union": 0, "union": separation / 2,
        "intersection": separation / 2,
        "difference": -(overlap * separation / 2) / (sphere_volume - overlap)}[operation]
    volume_error = abs(volume - expected_volume) / expected_volume
    centroid_error = float(np.linalg.norm(centroid - [expected_x, 0, 0]))

    def sdf(points):
        a = np.linalg.norm(points, axis=1) - radius
        b = np.linalg.norm(points - [separation, 0, 0], axis=1) - radius
        if operation in ("sphere", "self_union"):
            return a
        if operation == "union":
            return np.minimum(a, b)
        if operation == "difference":
            return np.maximum(a, -b)
        return np.maximum(a, b)

    forward = np.abs(sdf(np.concatenate([vertices, tris.mean(axis=1)])))
    indices = np.arange(400, dtype=float)
    z = 1 - 2 * (indices + 0.5) / len(indices)
    phi = indices * (math.pi * (3 - math.sqrt(5)))
    unit = np.stack([np.sqrt(1 - z*z) * np.cos(phi), np.sqrt(1 - z*z) * np.sin(phi), z], axis=1)
    ref = unit * radius
    if operation not in ("sphere", "self_union"):
        ref = np.concatenate([ref, ref + [separation, 0, 0]])
    ref = ref[np.abs(sdf(ref)) < 1e-12]
    reverse = np.concatenate([
        np.sqrt(((chunk[:, None, :] - vertices[None, :, :])**2).sum(axis=2).min(axis=1))
        for chunk in np.array_split(ref, max(1, math.ceil(len(ref) / 16)))
    ])
    # Face components, distinct from vertex-connected components.
    parents = list(range(len(faces)))

    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    owner = {}
    for face_index, face in enumerate(faces):
        for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            key = (min(a, b), max(a, b))
            if key in owner:
                parents[find(face_index)] = find(owner[key])
            else:
                owner[key] = face_index
    components = len({find(i) for i in range(len(faces))})
    chi = len(vertices) - len(unique_edges) + len(faces)
    normal_alignment = np.einsum("ij,ij->i", normals, cross) / np.maximum(double_area, 1e-300)
    passed = (nonmanifold == inconsistent == degenerate == duplicate_faces == nonfinite_normals == 0
        and components == 1 and chi == 2 and signed_volume > 0
        and float(normal_alignment.min()) > 0.999
        and volume_error <= 2 * (voxel / radius)**2 + 0.0005
        and centroid_error <= 2 * voxel and float(forward.max()) <= 1.5 * voxel)
    return {
        "pass": bool(passed), "triangleCount": len(tris), "vertexCount": len(vertices),
        "components": components, "eulerCharacteristic": chi,
        "nonmanifoldEdges": nonmanifold, "inconsistentEdges": inconsistent,
        "degenerateFaces": degenerate, "duplicateFaces": duplicate_faces,
        "nonfiniteNormals": nonfinite_normals,
        "signedVolumeM3": signed_volume, "analyticVolumeM3": expected_volume,
        "relativeVolumeError": volume_error, "centroidM": centroid.tolist(),
        "centroidErrorM": centroid_error, "boundsM": [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()],
        "forwardAnalyticSdfM": {"p95": float(np.percentile(forward, 95)), "max": float(forward.max()), "samples": len(forward)},
        "reverseNearestVertexUpperBoundM": {"p95": float(np.percentile(reverse, 95)), "max": float(reverse.max()), "samples": len(reverse)},
        "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "acceptanceScope": "P02 software fixture only; unverified exploratory mesh"
    }


def invoke(dotnet, worker, output, payload, timeout=45):
    started = time.perf_counter()
    process = subprocess.run(["/usr/bin/time", "-l", str(dotnet), str(worker), str(output)],
        input=payload, text=True, capture_output=True, timeout=timeout, check=False)
    events = [json.loads(line) for line in process.stdout.splitlines()]
    rss = re.search(r"(\d+)\s+maximum resident set size", process.stderr)
    return {"exitCode": process.returncode, "events": events, "stderr": process.stderr,
        "wallMs": (time.perf_counter() - started) * 1000,
        "maximumResidentBytes": int(rss[1]) if rss else None}


def request(operation="sphere", voxel=0.001, cycles=1):
    return {"schema": SCHEMA, "correlationId": str(uuid.uuid4()), "unit": "m",
        "frame": "right-handed-xyz", "operation": operation, "radiusM": 0.01,
        "separationM": 0.01, "voxelM": voxel, "cycles": cycles}


def run(args):
    fixtures = json.loads((HERE / "benchmark_fixtures.json").read_text())
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    cases = []
    for voxel in fixtures["voxelSizesM"]:
        for operation in fixtures["operations"]:
            req = request(operation, voxel)
            result = invoke(args.dotnet, args.worker, output / req["correlationId"], json.dumps(req))
            final = result["events"][-1]
            passed = result["exitCode"] == 0 and final["type"] == "completed"
            passed &= [e["type"] for e in result["events"]] == ["started", "completed"]
            passed &= all(e["correlationId"] == req["correlationId"] for e in result["events"])
            passed &= result["maximumResidentBytes"] is not None and result["maximumResidentBytes"] < fixtures["maximumResidentBytes"]
            qa = None
            if passed:
                cycle = final["cycles"][0]
                if operation in ("self_difference", "disjoint_intersection"):
                    passed &= cycle["empty"] and cycle["path"] is None and cycle["nativeVolumeM3"] == 0
                else:
                    qa = audit_mesh(cycle["path"], operation, 0.01, 0.01, voxel)
                    passed &= qa["pass"] and qa["sha256"] == cycle["sha256"] and not cycle["empty"]
            cases.append({"request": req, "pass": bool(passed), "run": result, "independentQa": qa})
    lifecycle_req = request(cycles=5)
    lifecycle = invoke(args.dotnet, args.worker, output / "lifecycle", json.dumps(lifecycle_req))
    lifecycle["pass"] = lifecycle["exitCode"] == 0 and len(lifecycle["events"][-1].get("cycles", [])) == 5

    negatives = []
    changes = [("schema", "unknown", "SCHEMA"), ("unit", "mm", "UNIT"),
        ("frame", "left-handed-xyz", "FRAME"), ("operation", "shell-command", "OPERATION"),
        ("radiusM", -1, "DIMENSION"), ("radiusM", 1, "DIMENSION"),
        ("voxelM", 0, "RESOLUTION"), ("voxelM", 1e-9, "RESOLUTION"),
        ("cycles", 100, "CYCLES"), ("correlationId", "not-a-uuid", "CORRELATION")]
    payloads = []
    for key, value, code in changes:
        req = request()
        req[key] = value
        payloads.append((f"invalid-{key}-{value}", json.dumps(req), code))
    base = request()
    payloads += [("oversized", " " * 8193, "REQUEST_TOO_LARGE"),
        ("malformed", "{", "INVALID_JSON"), ("nan", json.dumps({**base, "radiusM": math.nan}), "INVALID_JSON"),
        ("missing", json.dumps({k: v for k, v in base.items() if k != "separationM"}), "FIELDS"),
        ("extra", json.dumps({**base, "surprise": True}), "FIELDS"),
        ("duplicate", json.dumps(base)[:-1] + ',"unit":"m"}', "FIELDS")]
    for index, (name, payload, code) in enumerate(payloads):
        target = output / f"negative-{index}"
        result = invoke(args.dotnet, args.worker, target, payload)
        passed = result["exitCode"] == 2 and len(result["events"]) == 1
        passed &= result["events"][0].get("error", {}).get("code") == code
        passed &= not target.exists()
        negatives.append({"name": name, "expectedCode": code, "pass": bool(passed), "run": result})

    # Missing native runtime is a managed typed failure, not an application crash.
    missing = output / "missing-native-bin"
    missing.mkdir()
    for path in Path(args.worker).parent.glob("*"):
        if path.is_file() and path.suffix != ".dylib":
            shutil.copy2(path, missing / path.name)
    target = output / "missing-native-artifact"
    result = invoke(args.dotnet, missing / Path(args.worker).name, target, json.dumps(request()))
    passed = result["exitCode"] == 2 and result["events"][-1].get("error", {}).get("code") == "NATIVE_LOAD" and not target.exists()
    negatives.append({"name": "missing-native", "expectedCode": "NATIVE_LOAD", "pass": passed, "run": result})
    # Caller-enforced cancellation terminates this process and permits a clean retry.
    cancel_output = output / "cancelled"
    process = subprocess.Popen([str(args.dotnet), str(args.worker), str(cancel_output)], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    process.terminate()
    process.communicate(timeout=5)
    retry = invoke(args.dotnet, args.worker, output / "retry-after-cancel", json.dumps(request()))
    cancellation = {"exitCode": process.returncode, "pass": process.returncode != 0
        and not cancel_output.exists() and retry["exitCode"] == 0,
        "scope": "Termination before request ingestion; not mid-compute cancellation or atomic publish proof", "retry": retry}
    convergence = {}
    for operation in ("sphere", "union", "difference", "intersection"):
        errors = [case["independentQa"]["relativeVolumeError"] for case in cases
            if case["request"]["operation"] == operation and case["independentQa"]]
        convergence[operation] = {"errorsCoarseToFine": errors,
            "pass": len(errors) == 3 and errors[-1] < errors[0]}
    summary = {"schema": SCHEMA, "nativeSource": args.label, "cases": cases,
        "lifecycle": lifecycle, "negativeCases": negatives, "cancellation": cancellation,
        "convergence": convergence, "allPass": all(c["pass"] for c in cases + negatives)
            and lifecycle["pass"] and cancellation["pass"] and all(c["pass"] for c in convergence.values())}
    (HERE / args.result).write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"label": args.label, "fixtures": len(cases), "fixturesPass": sum(c["pass"] for c in cases),
        "negatives": len(negatives), "negativesPass": sum(c["pass"] for c in negatives),
        "lifecyclePass": lifecycle["pass"], "cancellationPass": cancellation["pass"],
        "allPass": summary["allPass"]}))
    return 0 if summary["allPass"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dotnet", type=Path, required=True)
    parser.add_argument("--worker", type=Path, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--result", required=True)
    raise SystemExit(run(parser.parse_args()))
