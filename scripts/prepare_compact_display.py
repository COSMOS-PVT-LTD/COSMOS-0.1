"""Create a bounded display derivative; keep original engine meshes unchanged.

No engineering topology/fidelity acceptance, smoothing of native CAD, runtime
admission or app-data writes. The manifest identifies the source native bytes.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from hashlib import sha256
from pathlib import Path

import numpy as np

from systems.geometry.qa import STL_RECORD


def prepare(native, output, python):
    root = Path(__file__).resolve().parents[1]
    manifest_path = native / "manifest.json"
    source = native / "UNQUALIFIED-export.stl"
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    if (
        manifest.get("schema") != "cosmos.compact-engine-build-evidence.v1"
        or manifest.get("complete") is not True
        or manifest.get("qualification") != "NOT_PERFORMED"
        or manifest.get("result", {}).get("backend") != "picogk"
        or manifest["result"].get("ok") is not True
        or source.is_symlink()
        or not 84 < source.stat().st_size <= 200_000_084
    ):
        raise ValueError("Bounded complete native compact research source required")
    digest = sha256(source.read_bytes()).hexdigest()
    if digest != manifest["artifacts"][source.name]:
        raise ValueError("Native source hash mismatch")
    parts, start = manifest["result"]["parts"], 0
    for part in parts:
        if (
            part["triangle_start"] != start
            or not 0 < part["triangle_count"] <= 4_000_000
        ):
            raise ValueError("Contiguous bounded native part spans required")
        start += part["triangle_count"]
    if (
        start != manifest["result"]["triangle_count"]
        or source.stat().st_size != 84 + start * 50
    ):
        raise ValueError("Native source length/triangle spans mismatch")
    if (
        not output.is_absolute()
        or output.exists()
        or output.is_symlink()
        or not output.parent.is_dir()
    ):
        raise ValueError("New absolute display folder required; no overwrite")
    if not python.is_absolute() or not python.is_file():
        raise ValueError("Explicit existing display-worker interpreter required")
    output.mkdir(mode=0o700)
    os.link(source, output / "input.stl")
    worker = root / "plugins/geometry/workers/pico_preview_worker.py"
    run = subprocess.run(
        [str(python), str(worker)],
        input=json.dumps({"parts": parts, "sha256": digest}),
        text=True,
        capture_output=True,
        timeout=180,
        cwd=output,
        env={**os.environ, "PYTHONPATH": str(root)},
        check=False,
    )
    with (output / "display-worker.log").open("x") as stream:
        stream.write(run.stderr)
    if run.returncode:
        raise ValueError(
            "Display reduction failed; original native CAD unchanged; inspect display-worker.log"
        )
    reduced = json.loads(run.stdout)
    positions = output / "positions.f32"
    data = positions.read_bytes()
    if sha256(data).hexdigest() != reduced["sha256"] or len(data) % 36:
        raise ValueError("Display bytes/hash mismatch")
    triangles = np.frombuffer(data, dtype="<f4").reshape(-1, 3, 3)
    if not 0 < len(triangles) <= 200_000 or not np.isfinite(triangles).all():
        raise ValueError("Finite bounded display positions required")
    faces = np.zeros(len(triangles), dtype=STL_RECORD)
    faces["vertices"] = triangles
    normals = np.cross(
        triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    )
    lengths = np.linalg.norm(normals, axis=1)
    if (lengths == 0).any():
        raise ValueError("Degenerate display triangles; no engineering-mesh repair")
    faces["normal"] = normals / lengths[:, None]
    display = output / "DISPLAY-ONLY-export.stl"
    with display.open("xb") as stream:
        stream.write(
            b"COSMOS DISPLAY DERIVATIVE ONLY; UNITS= m; NOT ENGINEERING CAD".ljust(
                80, b" "
            )
        )
        stream.write(len(triangles).to_bytes(4, "little"))
        stream.write(faces.tobytes())
    value = {
        "schema": "cosmos.compact-engine-display.v1",
        "complete": True,
        "qualification": "NOT_PERFORMED",
        "scope": "DISPLAY_DERIVATIVE_NOT_NATIVE_ENGINEERING_MESH",
        "recipe_sha256": manifest["recipe_sha256"],
        "source_commit_id": manifest["source_commit_id"],
        "native_manifest_sha256": sha256(raw).hexdigest(),
        "native_mesh_sha256": digest,
        "native_voxel_m": manifest["result"]["voxel_m"],
        "method": reduced["method"],
        "worker_sha256": sha256(worker.read_bytes()).hexdigest(),
        "result": {
            "ok": True,
            "backend": "picogk-display",
            "parts": reduced["parts"],
            "triangle_count": len(triangles),
        },
        "artifacts": {
            display.name: sha256(display.read_bytes()).hexdigest(),
            positions.name: reduced["sha256"],
        },
        "engineering_acceptance": "NOT_PERFORMED",
        "physical_validation": "NOT_PERFORMED",
    }
    with (output / "manifest.json").open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
    print(
        json.dumps(
            {"ok": True, "display_triangles": len(triangles), "output": str(output)}
        )
    )
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.native_dir, args.output, args.python)


if __name__ == "__main__":
    main()
