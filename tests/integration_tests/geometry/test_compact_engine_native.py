"""Explicit small new-feature tests, NOT an R08 or full-engine campaign."""

import json
import os
import subprocess

import numpy as np
import pytest

from systems.geometry.pico_mesh_qa import read_mesh
from tests.fixtures.compact_engine import joined_rings


def test_small_exact_union_variable_channel_and_gap_overlap_rejection(tmp_path):
    python = os.environ.get("COMPACT_OCCT_PYTHON")
    if not python:
        pytest.skip(
            "Explicit OCCT interpreter required; no runtime autodetection/admission"
        )
    code = """
import json
import sys
from pathlib import Path
from plugins.geometry.compact_occt import Builder
from scripts.generate_engine_redesign import occt_export
from tests.fixtures.compact_engine import joined_rings
c=joined_rings(); result=Builder(c.plan).build(c)
assert len(result)==1 and result[0][2]["valid"]
exports=occt_export(c,Path(sys.argv[1])); assert exports["step_file_unit"]=="mm"
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
reader=STEPControl_Reader(); assert reader.ReadFile(str(Path(sys.argv[1])/"UNQUALIFIED-assembly.step"))==IFSelect_RetDone
assert reader.TransferRoots()>0
volume,_=Builder.properties(reader.OneShape()); assert abs(volume-result[0][2]["volume_m3"])/volume<1e-8
for args in ({"gap":.0001},{"overlap":.0001}):
    c=joined_rings(**args)
    try: Builder(c.plan).build(c)
    except ValueError: pass
    else: raise AssertionError("Disconnected/overlapping operands accepted")
print(json.dumps(result[0][2]))
"""
    result = subprocess.run(
        [python, "-c", code, str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert json.loads(result.stdout.splitlines()[-1])["relative_integral_error"] < 1e-8


def test_small_native_picogk_union_has_closed_oriented_si_mesh(tmp_path):
    dotnet, worker = (
        os.environ.get("COMPACT_DOTNET"),
        os.environ.get("COMPACT_PICO_WORKER"),
    )
    if not dotnet or not worker:
        pytest.skip(
            "Explicit newly compiled PicoCompact worker required; old receipts are not admission"
        )
    c = joined_rings()
    request = {"research_only": True, "voxel_m": 0.00025, "recipe": c.wire()}
    result = subprocess.run(
        [dotnet, worker, str(tmp_path)],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    assert result.returncode == 0, (result.stdout[-2000:], result.stderr[-2000:])
    report = json.loads(result.stdout)
    assert report["qualification"] == "NOT_PERFORMED"
    assert report["triangle_count"] > 0
    _, mesh = read_mesh(tmp_path / "UNQUALIFIED-export.stl")
    triangles = mesh["vertices"].astype(float)
    vertices, ids = np.unique(triangles.reshape(-1, 3), axis=0, return_inverse=True)
    faces = ids.reshape(-1, 3)
    directed = np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    _, inverse, counts = np.unique(
        np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True
    )
    assert (counts == 2).all(), "Open/nonmanifold edges or phantom union seam"
    assert (
        np.bincount(inverse, weights=np.where(directed[:, 0] < directed[:, 1], 1, -1))
        == 0
    ).all()
    volume = (
        np.einsum(
            "ij,ij->i", triangles[:, 0], np.cross(triangles[:, 1], triangles[:, 2])
        ).sum()
        / 6
    )
    assert volume == pytest.approx(
        c.wire()["groups"][0]["reference_volume_m3"], rel=0.06
    )
    assert vertices[:, 0].min() > -0.0005 and vertices[:, 0].max() < 0.0045


def test_full_build_storage_guard_does_not_create_output(tmp_path, monkeypatch):
    import shutil

    from scripts.generate_engine_redesign import preflight

    monkeypatch.setattr(
        shutil,
        "disk_usage",
        lambda _: shutil._ntuple_diskusage(20 * 1024**3, 15 * 1024**3, 5 * 1024**3),
    )
    target = tmp_path / "must-not-be-created"
    with pytest.raises(ValueError, match="10GiB"):
        preflight(target)
    assert not target.exists()
