"""Tiny manufactured topology fixtures, never full-engine acceptance evidence."""

import json
from hashlib import sha256

import numpy as np
import pytest

from scripts import inspect_compact_regeneration as inspection
from systems.geometry.qa import STL_RECORD


def tetrahedra(*, two=False):
    vertices = (
        np.asarray(((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)), dtype="f4") * 0.001
    )
    faces = np.asarray(((0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)))
    triangles = vertices[faces]
    if two:
        triangles = np.concatenate((triangles, triangles + np.asarray((0.003, 0, 0))))
    records = np.zeros(len(triangles), dtype=STL_RECORD)
    records["vertices"] = triangles
    cross = np.cross(
        triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    )
    records["normal"] = cross / np.linalg.norm(cross, axis=1)[:, None]
    return records


def reference(*, two=False):
    return {
        "part_id": "manufactured-tetra",
        "reference_volume_m3": (2 if two else 1) * 0.001**3 / 6,
        "bounds_m": [0, 0, 0, 0.004 if two else 0.001, 0.001, 0.001],
    }


def write_stl(path, records):
    path.write_bytes(
        b"SOFTWARE FIXTURE; UNITS= m".ljust(80, b"\0")
        + len(records).to_bytes(4, "little")
        + records.tobytes()
    )


def test_closed_tetra_has_original_vertices_positive_integral_and_closed_oriented_edges():
    records = tetrahedra()
    before = records.tobytes()
    report = inspection.inspect_triangles(records, reference())
    assert report["topology_pass"]
    assert report["components"] == 1
    assert report["euler_characteristic_observed"] == 2
    assert report["signed_volume_m3"] == pytest.approx(0.001**3 / 6)
    assert report["relative_volume_error"] < 1e-6
    assert report["geometric_acceptance"] == "NOT_EVALUATED_NO_INTENDED_USE_LIMITS"
    assert records.tobytes() == before


@pytest.mark.parametrize(
    "mutation", ["open", "reversed", "duplicate", "degenerate", "disconnected"]
)
def test_actual_topology_defects_remain_failed_without_repairs(mutation):
    records = tetrahedra(two=mutation == "disconnected")
    if mutation == "open":
        records = records[:-1]
    elif mutation == "reversed":
        records[0]["vertices"] = records[0]["vertices"][[0, 2, 1]]
    elif mutation == "duplicate":
        records = np.concatenate((records, records[:1]))
    elif mutation == "degenerate":
        records[0]["vertices"][2] = records[0]["vertices"][1]
    report = inspection.inspect_triangles(
        records, reference(two=mutation == "disconnected")
    )
    assert not report["topology_pass"]
    if mutation == "disconnected":
        assert report["components"] == 2


def test_nonfinite_encoded_coordinates_refused():
    records = tetrahedra()
    records[0]["vertices"][0][0] = np.nan
    with pytest.raises(ValueError, match="Nonfinite"):
        inspection.inspect_triangles(records, reference())


def test_complete_native_mesh_span_and_units(tmp_path):
    path = tmp_path / "fixture.stl"
    write_stl(path, tetrahedra())
    result = {
        "triangle_count": 4,
        "parts": [
            {
                "part_id": "manufactured-tetra",
                "role": "metal",
                "triangle_start": 0,
                "triangle_count": 4,
            }
        ],
    }
    report = inspection.inspect_mesh(path, result, [reference()])
    assert report["topology_pass"] and report["repairs"] == "NONE"
    result["parts"][0]["triangle_start"] = 1
    with pytest.raises(ValueError, match="contiguous"):
        inspection.inspect_mesh(path, result, [reference()])


def test_bounded_mesh_does_not_accept_trailing_bytes_or_wrong_units(tmp_path):
    path = tmp_path / "fixture.stl"
    write_stl(path, tetrahedra())
    result = {
        "triangle_count": 4,
        "parts": [
            {
                "part_id": "manufactured-tetra",
                "role": "metal",
                "triangle_start": 0,
                "triangle_count": 4,
            }
        ],
    }
    path.write_bytes(path.read_bytes() + b"unexpected")
    with pytest.raises(ValueError, match="Complete bounded"):
        inspection.inspect_mesh(path, result, [reference()])
    write_stl(path, tetrahedra())
    path.write_bytes(path.read_bytes().replace(b"UNITS= m", b"UNITS=MM"))
    with pytest.raises(ValueError, match="metre units"):
        inspection.inspect_mesh(path, result, [reference()])


def test_manifest_requires_source_recipe_input_and_unchanged_native_bytes(tmp_path):
    class Candidate:
        @staticmethod
        def wire():
            return {"recipe_sha256": "a" * 64}

    artifact = tmp_path / "UNQUALIFIED-export.stl"
    write_stl(artifact, tetrahedra())
    manifest = {
        "schema": "cosmos.compact-engine-build-evidence.v1",
        "complete": True,
        "qualification": "NOT_PERFORMED",
        "recipe_sha256": "a" * 64,
        "source_commit_id": "source",
        "input_sha256": "b" * 64,
        "result": {"backend": "picogk", "ok": True},
        "artifacts": {artifact.name: sha256(artifact.read_bytes()).hexdigest()},
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    assert (
        inspection.native_manifest(
            tmp_path, Candidate(), {"source_commit_id": "source"}, "b" * 64, "picogk"
        )[1]
        == artifact
    )
    manifest["recipe_sha256"] = "c" * 64
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="exact research"):
        inspection.native_manifest(
            tmp_path, Candidate(), {"source_commit_id": "source"}, "b" * 64, "picogk"
        )
    manifest["recipe_sha256"] = "a" * 64
    path.write_text(json.dumps(manifest))
    artifact.write_bytes(artifact.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="SHA256"):
        inspection.native_manifest(
            tmp_path, Candidate(), {"source_commit_id": "source"}, "b" * 64, "picogk"
        )


def test_cli_refuses_existing_report_before_reading_artifacts(tmp_path, monkeypatch):
    import sys

    report = tmp_path / "existing.json"
    report.write_text("preserve")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "inspect",
            "--research-input",
            str(tmp_path / "input.json"),
            "--occt-dir",
            str(tmp_path / "occt"),
            "--picogk-dir",
            str(tmp_path / "picogk"),
            "--output",
            str(report),
        ],
    )
    with pytest.raises(SystemExit):
        inspection.main()
    assert report.read_text() == "preserve"
