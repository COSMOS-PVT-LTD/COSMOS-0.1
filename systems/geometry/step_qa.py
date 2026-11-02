"""Independent reader/process and analytic STEP fidelity checks, in SI metres."""
from __future__ import annotations

import json
import math
import re
import threading
from pathlib import Path
from typing import Any

import numpy as np

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from systems.contracts.geometry._wire import require

from .qa import FixtureReference


def audit_step(path: Path, reference: FixtureReference, *, reader: WorkerCommand, supervisor: WorkerSupervisor,
               job_id: str, tolerance_m: float, cancellation: threading.Event | None = None) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 64 * 1024**2,
            "INVALID_STEP", "Invalid/oversized independent STEP input")
    require(math.isfinite(tolerance_m) and tolerance_m > 0, "INVALID_TOLERANCE", "STEP QA requires positive finite SI tolerance")
    text = path.read_text()
    require(text.startswith("ISO-10303-21;") and text.rstrip().endswith("END-ISO-10303-21;") and "MANIFOLD_SOLID_BREP" in text and "CLOSED_SHELL" in text,
            "INVALID_STEP", "STEP is incomplete or lacks an analytic solid representation")
    require(re.search(r"LENGTH_UNIT\(\).*?SI_UNIT\(\$\s*,\s*\.METRE\.\)", text, re.DOTALL) is not None
            and ".MILLI." not in text and "FACETED_BREP" not in text, "INVALID_UNIT", "This qualified STEP profile requires analytic B-rep with metre units")
    samples = reference.surface_samples()
    result = supervisor.submit("qa-" + job_id, WorkerCommand((*reader.argv, str(path)), reader.environment),
                               json.dumps(samples.reshape(-1).tolist(), allow_nan=False).encode(), path.parent, cancellation=cancellation).result()
    require(result.code == "OK", result.code, "Independent STEP reader failed; do not accept export")
    def pairs(items):
        require(len({key for key, _ in items}) == len(items), "INVALID_RESPONSE", "Duplicate STEP observation key")
        return dict(items)
    try:
        data = json.loads(result.stdout, object_pairs_hook=pairs)
    except (ValueError, UnicodeError) as error:
        from systems.contracts.geometry import GeometryContractError
        raise GeometryContractError("INVALID_RESPONSE", "STEP reader emitted invalid JSON") from error
    expected = {"reader", "version", "units", "body_count", "volume_m3", "centroid_m", "bounds_m", "face_types", "face_count", "surface_samples_m", "reverse_distances_m", "boundary_count", "parametric_boundary_edges", "mesh_nonmanifold_edges", "mesh_orientation_errors", "mesh_triangle_count", "raw_face_types", "analytic_carrier_types", "face_classification", "import_unit", "bounds_method"}
    require(type(data) is dict and set(data) == expected and data["reader"] == "gmsh" and data["version"] == "4.15.0" and data["units"] == "m", "INVALID_RESPONSE", "Unexpected STEP reader/version/fields")
    require(type(data["body_count"]) is int and type(data["face_count"]) is int and type(data["boundary_count"]) is int,
            "INVALID_RESPONSE", "Invalid topology observations")
    require(all(type(data[key]) is int and data[key] >= 0 for key in ("parametric_boundary_edges", "mesh_nonmanifold_edges", "mesh_orientation_errors", "mesh_triangle_count"))
            and type(data["face_types"]) is list and all(type(item) is str for item in data["face_types"]), "INVALID_RESPONSE", "Invalid mesh/topology observation types")
    centroid = np.array(data["centroid_m"], dtype=float)
    bounds = np.array(data["bounds_m"], dtype=float)
    points = np.array(data["surface_samples_m"], dtype=float)
    reverse = np.array(data["reverse_distances_m"], dtype=float)
    require(centroid.shape == (3,) and bounds.shape == (6,) and 0 < points.size <= 60000 and points.size % 3 == 0
            and reverse.shape == (len(samples),) and all(bool(np.isfinite(v).all()) for v in (centroid, bounds, points, reverse))
            and bool((reverse >= 0).all()) and type(data["volume_m3"]) in (int, float) and np.isfinite(data["volume_m3"]), "INVALID_RESPONSE", "Invalid/nonfinite STEP metric shapes")
    points = points.reshape(-1, 3)
    volume_error = abs(data["volume_m3"]-reference.volume_m3)/reference.volume_m3
    centroid_error = float(np.linalg.norm(centroid-reference.centroid_m))
    bounds_error = float(np.max(np.abs(bounds-reference.bounds_m)))
    forward = np.abs(reference.sdf(points))
    expected_types = {"Plane", "Cylinder"} if reference.operation == "cylinder" else ({"Plane"} if reference.operation == "box" else {"Sphere"})
    expected_carriers = {"PLANE", "CYLINDRICAL_SURFACE"} if reference.operation == "cylinder" else ({"PLANE"} if reference.operation == "box" else {"SPHERICAL_SURFACE"})
    require(data["import_unit"] == "mm" and type(data["analytic_carrier_types"]) is list
            and type(data["raw_face_types"]) is list and len(data["raw_face_types"]) == data["face_count"]
            and type(data["face_classification"]) is list and type(data["bounds_method"]) is str,
            "INVALID_RESPONSE", "Missing explicit reader scale/classification evidence")
    topology = (data["body_count"] == 1 and data["face_count"] > 0 and data["boundary_count"] == data["face_count"]
                and data["mesh_nonmanifold_edges"] == data["mesh_orientation_errors"] == 0 and data["mesh_triangle_count"] > 0
                and set(data["face_types"]) == expected_types
                and len(data["analytic_carrier_types"]) == data["face_count"] and set(data["analytic_carrier_types"]) == expected_carriers)
    dimensions = (volume_error <= 1e-7 and centroid_error <= tolerance_m and bounds_error <= tolerance_m
                  and forward.max() <= tolerance_m and reverse.max() <= tolerance_m)
    return {"pass": bool(topology and dimensions), "topology_pass": topology, "dimensions_pass": bool(dimensions),
            "reader": "gmsh-4.15.0", "reader_kernel_independence": False,
            "independence_scope": "Different tool, API, process and import path; shared OCCT implementation plus independent analytic formulas",
            "body_count": data["body_count"], "face_count": data["face_count"], "face_types": data["face_types"],
            "raw_face_types": data["raw_face_types"], "analytic_carrier_types": data["analytic_carrier_types"],
            "face_classification": data["face_classification"], "import_unit": data["import_unit"], "bounds_method": data["bounds_method"],
            "mesh_nonmanifold_edges": data["mesh_nonmanifold_edges"], "mesh_orientation_errors": data["mesh_orientation_errors"],
            "parametric_boundary_edges": data["parametric_boundary_edges"],
            "file_units": "m", "volume_m3": data["volume_m3"], "relative_volume_error": volume_error, "relative_volume_limit": 1e-7,
            "centroid_m": centroid.tolist(), "centroid_error_m": centroid_error, "bounds_m": bounds.tolist(), "bounds_error_m": bounds_error,
            "forward_sample_count": len(forward), "forward_max_m": float(forward.max()), "forward_p95_m": float(np.percentile(forward, 95)),
            "reverse_sample_count": len(reverse), "reverse_max_m": float(reverse.max()), "reverse_p95_m": float(np.percentile(reverse, 95)),
            "distance_limit_m": tolerance_m, "sampling_scope": "Gmsh surface mesh nodes to analytic SDF; fixed analytic surface samples to Gmsh closest face projections; not certified Hausdorff",
            "physical_validation_claimed": False, "reader_observed_rss_bytes": result.maximum_rss_bytes}
