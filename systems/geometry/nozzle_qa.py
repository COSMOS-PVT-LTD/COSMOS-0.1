"""Explicit engineering-candidate software QA, not intended-use/hardware acceptance."""

from __future__ import annotations

import json
import math
import re
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from infrastructure.geometry import WorkerCommand
from plugins.geometry.nozzle_protocol import POLICY
from systems.contracts.geometry._wire import require
from systems.geometry.nozzle_reference import NozzleReference
from systems.geometry.qa import audit_mesh
from systems.geometry.service import GeometryBuildService


@dataclass(frozen=True)
class NozzleQALimits:
    relative_volume: float
    centroid_m: float
    distance_m: float
    source: str

    @classmethod
    def from_spec(cls, spec: dict[str, Any]):
        require(type(spec) is dict and set(spec) == {"relative_volume", "centroid", "surface_distance", "source"}, "INVALID_QA_POLICY", "Explicit volume/centroid/distance ceilings and intended-purpose source required")
        def scalar(value, unit):
            require(type(value) is dict and set(value) == {"value", "unit"} and value["unit"] == unit
                    and type(value["value"]) in (int, float) and math.isfinite(value["value"]) and 0 < value["value"] < .1,
                    "INVALID_QA_POLICY", "Explicit finite positive SI QA ceilings below the declared software envelope are required")
            return float(value["value"])
        require(type(spec["source"]) is str and 0 < len(spec["source"].strip()) <= 2048, "INVALID_QA_POLICY", "Bounded nonempty intended-purpose/tolerance source required")
        return cls(scalar(spec["relative_volume"], "1"), scalar(spec["centroid"], "m"), scalar(spec["surface_distance"], "m"), spec["source"])


class NozzleBuildService(GeometryBuildService):
    policy_id = POLICY
    reviewer_id = "r07-analytic-gmsh-software-audit"
    acceptance_stage = "software_candidate_qa"
    acceptance_message = "Nozzle candidate passes declared software QA; human engineering review and physical acceptance NOT_PERFORMED"

    def __init__(self, backend, candidate_root, *, step_reader, limits: NozzleQALimits):
        super().__init__(backend, candidate_root, step_reader=step_reader)
        self.limits = limits

    def validate_policy(self, snapshot, reference):
        require(isinstance(reference, NozzleReference) and snapshot.project_id.startswith("engine-design-"), "UNAPPROVED_POLICY", "Nozzle service requires its engine-derived exact analytic reference, not a fixture")

    def audit_candidate(self, path, format_, reference, request, job, token):
        require(isinstance(reference, NozzleReference), "UNAPPROVED_POLICY", "Nozzle reference required")
        assert isinstance(reference, NozzleReference)
        limits = self.limits
        if format_ == "stl":
            deadline = time.monotonic() + 60
            def budget():
                require(not token.is_set(), "CANCELLED", "Nozzle mesh QA cancelled; no candidate acceptance")
                require(time.monotonic() <= deadline, "QA_TIMEOUT", "Nozzle mesh QA exceeded its explicit 60-second local budget")
            result = audit_mesh(path, reference, voxel_m=None, export_tolerance_m=request.export_tolerance_m,
                                euler_characteristic=0, volume_ceiling=limits.relative_volume,
                                centroid_ceiling_m=limits.centroid_m, distance_ceiling_m=limits.distance_m, check_budget=budget)
            result["bidirectional_sampling_scope"] = "Actual STL vertices/face-centroids to exact meridian polygon; retained stations/midpoints, annular caps and eight azimuths to planar triangles with conservative AABB rejection outside the explicit ceiling. Unmatched samples fail, not invented distances. Not certified Hausdorff or self-intersection proof."
            return result
        require(self.step_reader is not None, "QA_UNAVAILABLE", "Independent nozzle STEP reimport reader required")
        text = path.read_text()
        require(text.startswith("ISO-10303-21;") and text.rstrip().endswith("END-ISO-10303-21;")
                and "MANIFOLD_SOLID_BREP" in text and "CLOSED_SHELL" in text
                and re.search(r"LENGTH_UNIT\(\).*?SI_UNIT\(\$\s*,\s*\.METRE\.\)", text, re.DOTALL) is not None
                and ".MILLI." not in text and "FACETED_BREP" not in text, "INVALID_STEP", "Complete analytic solid STEP in metres required; no mesh/CAD relabelling")
        command = WorkerCommand((*self.step_reader.argv, str(path)), self.step_reader.environment)
        run = self.backend.supervisor.submit("qa-" + job, command,
                    json.dumps({"samples_m": reference.surface_samples().tolist(), "distance_limit_m": limits.distance_m}, allow_nan=False).encode(),
                    path.parent, cancellation=token).result()
        require(run.code == "OK", run.code, "Independent nozzle STEP reader failed; no accepted artifact")
        data = json.loads(run.stdout)
        fields = {"reader", "version", "units", "import_unit", "body_count", "face_count", "face_types", "analytic_carrier_types", "volume_m3", "centroid_m", "bounds_m", "surface_samples_m", "reverse_distances_m", "unmatched_reverse_samples", "mesh_nonmanifold_edges", "mesh_orientation_errors", "mesh_triangle_count", "mesh_euler_characteristic", "boundary_face_count", "bbox_deflection_m", "sampling_scope"}
        require(type(data) is dict and set(data) == fields, "INVALID_RESPONSE", "Exact bounded nozzle reimport response fields required")
        require(data["reader"] == "gmsh" and data["version"] == "4.15.0" and data["units"] == "m" and data["import_unit"] == "mm", "INVALID_RESPONSE", "Unexpected independent reader/units/version")
        def finite(value):
            return type(value) in (int, float) and math.isfinite(value)
        require(all(type(data[key]) is int and 0 <= data[key] <= 100000 for key in ("body_count", "face_count", "boundary_face_count", "unmatched_reverse_samples", "mesh_nonmanifold_edges", "mesh_orientation_errors", "mesh_triangle_count", "mesh_euler_characteristic"))
                and finite(data["volume_m3"]) and data["volume_m3"] > 0 and finite(data["bbox_deflection_m"]) and 0 < data["bbox_deflection_m"] <= limits.distance_m / 10,
                "INVALID_RESPONSE", "Independent response counts, volume and sampling deflection must be finite and bounded")
        require(all(type(data[key]) is list and len(data[key]) == size and all(finite(v) for v in data[key]) for key, size in (("centroid_m", 3), ("bounds_m", 6)))
                and type(data["surface_samples_m"]) is list and 0 < len(data["surface_samples_m"]) <= 20000
                and all(type(row) is list and len(row) == 3 and all(finite(v) for v in row) for row in data["surface_samples_m"])
                and type(data["reverse_distances_m"]) is list and len(data["reverse_distances_m"]) == len(reference.surface_samples())
                and all(type(data[key]) is list and len(data[key]) == data["face_count"] and all(type(v) is str and 0 < len(v) <= 128 for v in data[key]) for key in ("face_types", "analytic_carrier_types"))
                and type(data["sampling_scope"]) is str and 0 < len(data["sampling_scope"]) <= 2048,
                "INVALID_RESPONSE", "Exact bounded finite SI vector/sample shapes and analytic face descriptors required")
        require(data["unmatched_reverse_samples"] == 0 and all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in data["reverse_distances_m"]), "REIMPORT_DISTANCE_UNAVAILABLE", "Imported trimmed faces do not cover every requested reference sample within the explicit ceiling")
        forward = np.abs(reference.sdf(data["surface_samples_m"]))
        reverse = np.array(data["reverse_distances_m"])
        require(len(reverse) == len(reference.surface_samples()) and 0 < len(forward) <= 20000
                and np.isfinite(forward).all() and np.isfinite(reverse).all(), "INVALID_RESPONSE", "Nonfinite or mismatched independent surface samples")
        volume_error = abs(data["volume_m3"] - reference.volume_m3) / reference.volume_m3
        centroid_error = float(np.linalg.norm(np.array(data["centroid_m"]) - reference.centroid_m))
        bounds_error = float(np.max(np.abs(np.array(data["bounds_m"]) - reference.bounds_m)))
        carriers = data["analytic_carrier_types"]
        topology = (data["body_count"] == 1 and data["face_count"] == 2 * len(reference.profile.points)
                    and data["boundary_face_count"] == data["face_count"] and len(carriers) == data["face_count"]
                    and set(carriers) <= {"PLANE", "CONICAL_SURFACE", "CYLINDRICAL_SURFACE", "SURFACE_OF_REVOLUTION"}
                    and carriers.count("PLANE") == 2 and data["mesh_nonmanifold_edges"] == data["mesh_orientation_errors"] == 0
                    and data["mesh_euler_characteristic"] == 0 and data["mesh_triangle_count"] > 0)
        dimensions = volume_error <= limits.relative_volume and centroid_error <= limits.centroid_m and bounds_error <= limits.distance_m and forward.max() <= limits.distance_m and reverse.max() <= limits.distance_m
        return {"pass": bool(topology and dimensions), "topology_pass": bool(topology), "dimensions_pass": bool(dimensions),
                "reader": "gmsh-4.15.0", "reader_kernel_independence": False, "independence_scope": "Separate tool/API/import/process plus kernel-independent polygon-of-revolution formulas; Gmsh and OCP share OCCT implementation",
                "body_count": data["body_count"], "face_count": data["face_count"], "analytic_carrier_types": carriers, "face_types": data["face_types"],
                "relative_volume_error": volume_error, "relative_volume_limit": limits.relative_volume, "centroid_error_m": centroid_error, "centroid_limit_m": limits.centroid_m,
                "bounds_error_m": bounds_error, "distance_limit_m": limits.distance_m, "forward_max_m": float(forward.max()), "forward_p95_m": float(np.percentile(forward, 95)), "forward_samples": len(forward),
                "reverse_max_m": float(reverse.max()), "reverse_p95_m": float(np.percentile(reverse, 95)), "reverse_samples": len(reverse), "sampling_scope": data["sampling_scope"],
                "observations": {key: data[key] for key in ("mesh_nonmanifold_edges", "mesh_orientation_errors", "mesh_euler_characteristic", "mesh_triangle_count", "bbox_deflection_m")},
                "reader_observed_rss_bytes": run.maximum_rss_bytes, "physical_validation_claimed": False}
