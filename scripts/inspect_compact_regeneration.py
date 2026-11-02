"""Independent research checks for a retained compact STEP/native PicoGK build.

Never repairs a mesh, changes a baseline or admits a runtime. Numerical volume
comparison reuses the generator's 1e-6 software integral check, not an engineering
tolerance. Mesh deviations are observations without intended-use acceptance.
"""

from __future__ import annotations

import argparse
import json
import math
from hashlib import sha256
from pathlib import Path

import numpy as np

from scripts.generate_engine_redesign import load_candidate, unique
from systems.geometry.qa import STL_RECORD

MAX_TRIANGLES = 4_000_000
MAX_NATIVE_BYTES = 84 + 50 * MAX_TRIANGLES
GENERATOR_VOLUME_RELATIVE_TOLERANCE = 1e-6


def checked_file(path: Path, maximum: int) -> Path:
    if (
        not path.is_file()
        or path.is_symlink()
        or not 0 < path.stat().st_size <= maximum
    ):
        raise ValueError(f"Missing, linked or oversized input artifact: {path}")
    return path


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def native_manifest(
    directory: Path, candidate, input_record: dict, input_hash: str, backend: str
):
    path = checked_file(directory / "manifest.json", 2 * 1024**2)
    value = json.loads(path.read_text(), object_pairs_hook=unique)
    if (
        value.get("schema") != "cosmos.compact-engine-build-evidence.v1"
        or value.get("complete") is not True
        or value.get("qualification") != "NOT_PERFORMED"
        or value.get("recipe_sha256") != candidate.wire()["recipe_sha256"]
        or value.get("source_commit_id") != input_record["source_commit_id"]
        or value.get("input_sha256") != input_hash
        or value.get("result", {}).get("backend") != backend
        or value.get("result", {}).get("ok") is not True
    ):
        raise ValueError(
            "Completed native manifest must match the exact research input, source and recipe"
        )
    filename = (
        "UNQUALIFIED-assembly.step" if backend == "occt" else "UNQUALIFIED-export.stl"
    )
    artifact = checked_file(directory / filename, 512 * 1024**2)
    if value.get("artifacts", {}).get(filename) != file_sha256(artifact):
        raise ValueError(
            "Native artifact SHA256 disagrees with its source-bound manifest"
        )
    return value, artifact


def _components(edges: np.ndarray, vertex_count: int) -> int:
    """Exact encoded vertex connectivity, without epsilon welding."""
    parents = np.arange(vertex_count, dtype=np.int64)
    sizes = np.ones(vertex_count, dtype=np.int64)

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for left, right in edges:
        left, right = find(left), find(right)
        if left != right:
            if sizes[left] < sizes[right]:
                left, right = right, left
            parents[right] = left
            sizes[left] += sizes[right]
    return int(np.count_nonzero(parents == np.arange(vertex_count)))


def inspect_triangles(records: np.ndarray, reference: dict) -> dict:
    """Topology/integrals of ONE unchanged encoded part; bounded part lifetime."""
    count = len(records)
    if not 0 < count <= MAX_TRIANGLES:
        raise ValueError("Bounded nonempty native triangle span required")
    triangles = records["vertices"]
    normals = records["normal"]
    if not np.isfinite(triangles).all() or not np.isfinite(normals).all():
        raise ValueError("Nonfinite native vertices/normals; no repair performed")
    if np.abs(triangles).max() > 10:
        raise ValueError(
            "Native metre coordinates exceed the source coordinate envelope"
        )
    vertices, ids = np.unique(triangles.reshape(-1, 3), axis=0, return_inverse=True)
    faces = ids.reshape(-1, 3)
    directed = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    edges, inverse, incidences = np.unique(
        np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True
    )
    orientation = np.bincount(
        inverse, weights=np.where(directed[:, 0] < directed[:, 1], 1, -1)
    )
    del inverse, directed
    components = _components(edges, len(vertices))
    duplicate_faces = count - len(np.unique(np.sort(faces, axis=1), axis=0))
    volume_terms, degenerate_faces, wrong_normals, surface_area = [], 0, 0, 0.0
    # Float64 integration only per chunk; do not retain a full double mesh.
    for start in range(0, count, 32768):
        tri = triangles[start : start + 32768].astype(np.float64)
        cross = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        lengths = np.linalg.norm(cross, axis=1)
        degenerate_faces += int(np.count_nonzero(lengths == 0))
        wrong_normals += int(
            np.count_nonzero(
                np.einsum("ij,ij->i", normals[start : start + len(tri)], cross) <= 0
            )
        )
        volume_terms.append(
            float(
                np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum()
                / 6
            )
        )
        surface_area += float(lengths.sum() / 2)
    volume = math.fsum(volume_terms)
    bounds = np.r_[vertices.min(axis=0), vertices.max(axis=0)].astype(float)
    expected_volume = reference["reference_volume_m3"]
    expected_bounds = np.asarray(reference["bounds_m"], dtype=float)
    topology = bool(
        components == 1
        and np.all(incidences == 2)
        and np.all(orientation == 0)
        and degenerate_faces == 0
        and duplicate_faces == 0
        and wrong_normals == 0
        and math.isfinite(volume)
        and volume > 0
    )
    return {
        "part_id": reference["part_id"],
        "triangle_count": count,
        "topology_pass": topology,
        "components": components,
        "vertex_count": len(vertices),
        "edge_count": len(edges),
        "euler_characteristic_observed": int(len(vertices) - len(edges) + count),
        "non_two_incidence_edges": int(np.count_nonzero(incidences != 2)),
        "orientation_errors": int(np.count_nonzero(orientation)),
        "degenerate_faces": degenerate_faces,
        "duplicate_faces": int(duplicate_faces),
        "nonpositive_normal_alignment_faces": wrong_normals,
        "signed_volume_m3": volume,
        "reference_volume_m3": expected_volume,
        "relative_volume_error": abs(volume - expected_volume) / expected_volume,
        "surface_area_m2": surface_area,
        "bounds_m": bounds.tolist(),
        "reference_bounds_m": expected_bounds.tolist(),
        "bounds_max_difference_m": float(np.abs(bounds - expected_bounds).max()),
        "geometric_acceptance": "NOT_EVALUATED_NO_INTENDED_USE_LIMITS",
        "vertices_modified": False,
    }


def inspect_mesh(path: Path, result: dict, groups: list[dict]) -> dict:
    checked_file(path, MAX_NATIVE_BYTES)
    with path.open("rb") as stream:
        header = stream.read(84)
    count = int.from_bytes(header[80:84], "little")
    if (
        b"UNITS= m" not in header[:80]
        or not 0 < count <= MAX_TRIANGLES
        or path.stat().st_size != 84 + 50 * count
    ):
        raise ValueError(
            "Complete bounded binary STL with explicit metre units required"
        )
    expected = {group["part_id"]: group for group in groups}
    parts = result.get("parts")
    if (
        not isinstance(parts, list)
        or len(parts) != len(expected)
        or result.get("triangle_count") != count
    ):
        raise ValueError(
            "Native part count/triangle count must match the exact candidate"
        )
    cursor, seen = 0, set()
    for part in parts:
        if (
            not isinstance(part, dict)
            or part.get("part_id") not in expected
            or part["part_id"] in seen
            or part.get("role") != "metal"
            or type(part.get("triangle_start")) is not int
            or part["triangle_start"] != cursor
            or type(part.get("triangle_count")) is not int
            or part["triangle_count"] <= 0
        ):
            raise ValueError(
                "Unique contiguous native part spans required; no inferred/repaired mapping"
            )
        seen.add(part["part_id"])
        cursor += part["triangle_count"]
    if cursor != count:
        raise ValueError("Native part spans must cover every encoded triangle exactly")
    records = np.memmap(path, mode="r", dtype=STL_RECORD, offset=84, shape=(count,))
    observations = []
    for part in parts:
        start, size = part["triangle_start"], part["triangle_count"]
        observations.append(
            inspect_triangles(records[start : start + size], expected[part["part_id"]])
        )
    del records
    return {
        "topology_pass": all(p["topology_pass"] for p in observations),
        "parts": observations,
        "triangle_count": count,
        "file_units": "m",
        "repairs": "NONE",
        "dimensional_acceptance": "NOT_EVALUATED_NO_INTENDED_USE_LIMITS",
    }


def inspect_step(path: Path, groups: list[dict]) -> dict:
    """A new STEP reader, not the writer's returned native shapes."""
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPControl import STEPControl_Reader
    from OCP.TColStd import TColStd_SequenceOfAsciiString
    from OCP.TopAbs import TopAbs_SOLID
    from OCP.TopExp import TopExp_Explorer

    checked_file(path, 512 * 1024**2)
    reader = STEPControl_Reader()
    if reader.ReadFile(str(path)) != IFSelect_RetDone:
        raise ValueError("Independent STEP reader could not read the exported file")
    length, angle, solid_angle = (TColStd_SequenceOfAsciiString() for _ in range(3))
    reader.FileUnits(length, angle, solid_angle)
    units = [length.Value(i).ToCString() for i in range(1, length.Length() + 1)]
    unit_pass = bool(units) and all(
        v.lower() in {"millimetre", "millimeter", "mm"} for v in units
    )
    reader.SetSystemLengthUnit(1.0)  # OCCT millimetres, explicitly set before transfer.
    if reader.TransferRoots() <= 0:
        raise ValueError("Independent STEP transfer produced no roots")
    shape = reader.OneShape()
    whole_valid = BRepCheck_Analyzer(shape, True).IsValid()
    explorer, solids = TopExp_Explorer(shape, TopAbs_SOLID), []
    while explorer.More():
        solid = explorer.Current()
        properties, bounds = GProp_GProps(), Bnd_Box()
        BRepGProp.VolumeProperties_s(solid, properties)
        BRepBndLib.AddOptimal_s(solid, bounds, False, False)
        solids.append(
            {
                "volume_m3": properties.Mass() * 1e-9,
                "valid": bool(BRepCheck_Analyzer(solid, True).IsValid()),
                "bounds_m": (np.asarray(bounds.Get()) * 0.001).tolist(),
            }
        )
        explorer.Next()
    # Basic STEP AsIs export does not retain a governed semantic part mapping.
    # Pair by sorted independent volume only; do not claim identity from face IDs.
    solids.sort(key=lambda item: item["volume_m3"])
    references = sorted(groups, key=lambda item: item["reference_volume_m3"])
    observations = []
    for actual, reference in zip(solids, references):
        expected = reference["reference_volume_m3"]
        observations.append(
            {
                **actual,
                "reference_part_id_by_volume_order": reference["part_id"],
                "reference_volume_m3": expected,
                "relative_volume_error": abs(actual["volume_m3"] - expected) / expected,
                "reference_bounds_m": reference["bounds_m"],
                "bounds_max_difference_m": float(
                    np.abs(np.asarray(actual["bounds_m"]) - reference["bounds_m"]).max()
                ),
            }
        )
    passed = bool(
        whole_valid
        and unit_pass
        and len(solids) == len(groups)
        and all(
            row["valid"]
            and row["volume_m3"] > 0
            and row["relative_volume_error"] <= GENERATOR_VOLUME_RELATIVE_TOLERANCE
            for row in observations
        )
    )
    return {
        "software_reimport_checks_pass": passed,
        "whole_shape_valid": bool(whole_valid),
        "solid_count": len(solids),
        "expected_solid_count": len(groups),
        "length_units_reported_by_reader": units,
        "file_unit_check_pass": unit_pass,
        "reader_internal_length_unit": "mm",
        "reported_measurements_unit": "m",
        "part_association": "SORTED_VOLUME_OBSERVATION_NOT_SEMANTIC_IDENTITY",
        "numerical_volume_relative_tolerance": GENERATOR_VOLUME_RELATIVE_TOLERANCE,
        "numerical_tolerance_source": "plugins/geometry/compact_occt.py Builder.build existing software integral check",
        "parts": observations,
    }


def inspect_campaign(research_input: Path, occt_dir: Path, picogk_dir: Path) -> dict:
    checked_file(research_input, 2 * 1024**2)
    candidate, value, checksum = load_candidate(research_input)
    groups = candidate.wire()["groups"]
    report = {
        "schema": "cosmos.compact-regeneration-research-inspection.v1",
        "recipe_sha256": candidate.wire()["recipe_sha256"],
        "research_input_sha256": checksum,
        "source_commit_id": value["source_commit_id"],
        "qualification": "NOT_PERFORMED",
        "r08": "ON_HOLD",
        "engineering_acceptance": "NOT_PERFORMED",
        "physical_validation": "NOT_PERFORMED",
        "scope": "Independent STEP reimport and unchanged native STL topology/integrals; not self-intersection proof, certified surface distance, feature coverage or manufacturing acceptance",
        "software_checks_scope": "STEP numerical integral/unit/validity checks plus native STL basic topology only; native mesh dimensional deviations are reported without intended-use acceptance",
    }
    for backend, directory in (("occt", occt_dir), ("picogk", picogk_dir)):
        try:
            manifest, path = native_manifest(
                directory, candidate, value, checksum, backend
            )
            report[backend] = (
                inspect_step(path, groups)
                if backend == "occt"
                else inspect_mesh(path, manifest["result"], groups)
            )
        except Exception as error:  # noqa: BLE001 -- retain native inspection errors per backend, never promote a failure
            report[backend] = {
                "inspection_completed": False,
                "error_type": type(error).__name__,
                "error": str(error),
            }
    report["software_checks_pass"] = bool(
        report["occt"].get("software_reimport_checks_pass")
        and report["picogk"].get("topology_pass")
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-input", type=Path, required=True)
    parser.add_argument("--occt-dir", type=Path, required=True)
    parser.add_argument("--picogk-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if any(
        not path.is_absolute()
        for path in (args.research_input, args.occt_dir, args.picogk_dir, args.output)
    ):
        parser.error("Explicit absolute source/artifact/output paths required")
    if (
        args.output.exists()
        or args.output.is_symlink()
        or not args.output.parent.is_dir()
    ):
        parser.error("New output file with existing parent required; no overwrite")
    report = inspect_campaign(args.research_input, args.occt_dir, args.picogk_dir)
    report["inspection_method_sha256"] = file_sha256(Path(__file__))
    with args.output.open("x") as stream:
        json.dump(report, stream, allow_nan=False, indent=2)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "software_checks_pass": report["software_checks_pass"],
                "qualification": "NOT_PERFORMED",
            }
        )
    )


if __name__ == "__main__":
    main()
