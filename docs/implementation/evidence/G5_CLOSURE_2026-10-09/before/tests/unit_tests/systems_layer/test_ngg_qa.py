import math
import sys

import numpy as np
import pytest

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from systems.contracts.geometry import GeometryContractError
from systems.geometry.qa import (
    STL_RECORD,
    FixtureReference,
    audit_mesh,
    condition_exact_zero_faces,
    distances_to_triangles,
    read_stl,
)
from systems.geometry.step_qa import audit_step


def write_stl(path, triangles, *, normals=None):
    records = np.zeros(len(triangles), dtype=STL_RECORD)
    records["vertices"] = triangles
    if normals is None:
        cross = np.cross(records["vertices"][:, 1] - records["vertices"][:, 0], records["vertices"][:, 2] - records["vertices"][:, 0])
        lengths = np.linalg.norm(cross, axis=1)
        records["normal"] = cross / np.where(lengths == 0, 1, lengths)[:, None]
    else:
        records["normal"] = normals
    path.write_bytes(b"COSMOS software fixture UNITS= m".ljust(80, b" ") + len(records).to_bytes(4, "little") + records.tobytes())


@pytest.mark.parametrize("operation", ["sphere", "box", "cylinder", "union", "difference", "intersection", "self_union"])
def test_predeclared_independent_analytic_references(operation):
    reference = FixtureReference(operation)
    samples = reference.surface_samples()
    assert reference.volume_m3 > 0 and np.max(np.abs(reference.sdf(samples))) < 1e-14
    assert len(samples) >= 100 and reference.bounds_m.shape == (6,)
    assert np.all(samples.min(axis=0) >= reference.bounds_m[:3] - 1e-14)
    assert np.all(samples.max(axis=0) <= reference.bounds_m[3:] + 1e-14)


@pytest.mark.parametrize("kwargs", [{"operation": "engine"}, {"operation": "sphere", "radius_m": .02}, {"operation": "sphere", "separation_m": .02}])
def test_fixture_policy_is_not_general_engineering_approval(kwargs):
    with pytest.raises(GeometryContractError):
        FixtureReference(**kwargs)


def test_point_triangle_distance_uses_faces_edges_and_vertices():
    triangles = np.array([[[0., 0, 0], [1, 0, 0], [0, 1, 0]]])
    points = np.array([[.2, .2, 2], [.5, -.5, 0], [-1, -1, 0], [.5, .5, 0]])
    assert np.allclose(distances_to_triangles(points, triangles), [2, .5, math.sqrt(2), 0])


@pytest.mark.parametrize("defect", ["units", "count", "nonfinite", "short", "symlink"])
def test_independent_mesh_parser_rejects_bad_files(tmp_path, defect):
    path = tmp_path / "source.stl"
    write_stl(path, [[[0, 0, 0], [1, 0, 0], [0, 1, 0]]])
    data = path.read_bytes()
    if defect == "units":
        path.write_bytes(b"wrong".ljust(80, b" ") + data[80:])
    elif defect == "count":
        path.write_bytes(data[:80] + (200001).to_bytes(4, "little") + data[84:])
    elif defect == "nonfinite":
        write_stl(path, [[[float("nan"), 0, 0], [1, 0, 0], [0, 1, 0]]], normals=[[0, 0, 1]])
    elif defect == "short":
        path.write_bytes(data[:-1])
    else:
        link = tmp_path / "link.stl"; link.symlink_to(path); path = link
    with pytest.raises(GeometryContractError):
        read_stl(path)


def test_exact_zero_conditioning_is_explicit_bounded_and_vertex_preserving(tmp_path):
    source, target = tmp_path / "raw.stl", tmp_path / "conditioned.stl"
    face = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
    write_stl(source, [face]*100 + [[[0, 0, 0]]*3], normals=[[0, 0, 1]]*100 + [[float("nan")]*3])
    original = source.read_bytes()
    report = condition_exact_zero_faces(source, target)
    assert report["removed_exact_zero_faces"] == 1 and report["surviving_vertices_identical"]
    assert report["positive_area_epsilon"] is None and not report["voxel_refinement"]
    assert source.read_bytes() == original
    assert np.array_equal(read_stl(source, allow_bad_normals=True)[1][:-1], read_stl(target)[1])
    with pytest.raises(GeometryContractError):
        condition_exact_zero_faces(source, target)


def test_excess_degeneracy_is_refused_without_writing(tmp_path):
    source, target = tmp_path / "raw.stl", tmp_path / "conditioned.stl"
    write_stl(source, [[[0, 0, 0]]*3, [[0, 0, 0], [1, 0, 0], [0, 1, 0]]])
    with pytest.raises(GeometryContractError) as error:
        condition_exact_zero_faces(source, target)
    assert error.value.code == "EXCESS_DEGENERACY" and not target.exists()


@pytest.mark.parametrize("tolerance", [0, -1, float("nan"), float("inf")])
def test_invalid_qa_tolerances_never_infer_defaults(tmp_path, tolerance):
    with pytest.raises(GeometryContractError):
        audit_mesh(tmp_path / "missing.stl", FixtureReference("sphere"), voxel_m=None, export_tolerance_m=tolerance)


@pytest.mark.parametrize("text", ["truncated", "ISO-10303-21; MANIFOLD_SOLID_BREP CLOSED_SHELL LENGTH_UNIT() SI_UNIT(.MILLI.,.METRE.) END-ISO-10303-21;"])
def test_bad_step_rejected_before_native_reader(tmp_path, text):
    path = tmp_path / "export.step"; path.write_text(text)
    with WorkerSupervisor() as supervisor, pytest.raises(GeometryContractError):
        audit_step(path, FixtureReference("sphere"), reader=WorkerCommand((sys.executable, "-c", "raise RuntimeError('must not execute')")), supervisor=supervisor, job_id="test", tolerance_m=1e-6)
