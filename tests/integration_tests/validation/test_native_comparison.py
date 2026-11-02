"""Actual native kernel evidence. Opt-in; mocks cannot satisfy G8 native proof."""
import base64
import os
from pathlib import Path

import pytest

from api.ngg_workbench import runtime_config
from systems.contracts.geometry._wire import GeometryContractError
from systems.geometry.workbench import GeometryWorkbench
from validation.workbench import ComparisonWorkbench

ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.skipif(os.environ.get("COSMOS_P10_NATIVE") != "1", reason="Explicit qualified native runtime required; run separately for G8")


@pytest.fixture(scope="module")
def native(tmp_path_factory):
    root = tmp_path_factory.mktemp("p10-native")
    config = runtime_config(ROOT / "docs/implementation/evidence/P08_2026-10-09/local-runtime.json")
    geometry = GeometryWorkbench(root, config); w = ComparisonWorkbench(root)
    a = geometry.context("test"); job = geometry.build("test", a["snapshot"]["content_sha256"])
    geometry.owned("test", job["job_id"])[1].result(timeout=60)
    left = w.capture("test", geometry, job["job_id"], job["snapshot_id"])
    b = geometry.change("test", job["snapshot_id"], {"backend": "picogk", "operation": "sphere", "voxel_m": .0005})
    other = geometry.build("test", b["snapshot"]["content_sha256"])
    geometry.owned("test", other["job_id"])[1].result(timeout=60)
    right = w.capture("test", geometry, other["job_id"], other["snapshot_id"])
    yield w, geometry, left, right
    w.close(); geometry.close()


def test_actual_occt_picogk_cross_kernel_dimensions_and_provenance(native):
    w, _, a, b = native
    report = w.compare_geometry("test", a["geometry_id"], b["geometry_id"])["report"]
    assert report["comparison_passed"] and report["cross_kernel"]
    assert report["left"]["qa"]["pass"] and report["right"]["qa"]["pass"]
    assert report["experimental_validation"] == "not-performed" and report["production_handoff"] is False


def test_actual_external_step_import_independent_reader_not_independent_kernel(native):
    w, g, _, _ = native
    path = ROOT / "docs/implementation/evidence/P09_2026-10-10/handoff-exact-sphere.step"
    value = w.import_step("test", g, base64.b64encode(path.read_bytes()).decode(), {"source": "retained P09 native STEP fixture", "author": "COSMOS software fixture", "license": "repository license"})
    result = w.session("test").imports[value["import_id"]].result(timeout=60)
    assert result["qa"]["pass"] and result["qa"]["reader_kernel_independence"] is False
    assert result["source_sha256"] == __import__("hashlib").sha256(path.read_bytes()).hexdigest()


def test_changed_fixture_or_identical_bytes_cannot_compare(native):
    w, _, a, _ = native
    with pytest.raises(GeometryContractError): w.compare_geometry("test", a["geometry_id"], a["geometry_id"])


def test_tampered_captured_export_is_rejected_before_comparison(native):
    w, _, a, b = native
    path, _ = w.session("test").files[a["geometry_id"]]
    raw = path.read_bytes()
    try:
        path.write_bytes(raw + b"\n")
        with pytest.raises(GeometryContractError): w.compare_geometry("test", a["geometry_id"], b["geometry_id"])
    finally:
        path.write_bytes(raw)
