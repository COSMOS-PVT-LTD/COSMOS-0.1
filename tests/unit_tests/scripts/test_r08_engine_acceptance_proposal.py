"""Offline planning checks; these are NOT additional native engine qualification."""

import json
from hashlib import sha256

import pytest

from scripts.prepare_r08_engine_acceptance_proposal import CAPTURE_SHA, ROOT, prepare
from systems.geometry.qualification_policy import validate


@pytest.fixture(scope="module")
def proposal():
    root = ROOT / "output/picogk-components-2026-10-24/final-generation-evidence"
    capture, baseline = root / "captured-inputs.json", root / "summary.json"
    before = [sha256(p.read_bytes()).hexdigest() for p in (capture, baseline)]
    result = prepare(capture, baseline, CAPTURE_SHA)
    assert before == [sha256(p.read_bytes()).hexdigest() for p in (capture, baseline)]
    return result


def test_draft_cannot_be_mistaken_for_runtime_policy_or_approval(proposal):
    assert proposal["status"] == "DRAFT_NOT_APPROVED_NOT_EXECUTABLE"
    assert not any(
        proposal[k]
        for k in ("approval_recorded", "app_data_written", "native_campaign_executed")
    )
    with pytest.raises(ValueError):
        validate(proposal, None)


def test_all_sixteen_exact_parts_are_preserved_and_every_batch_is_bounded(proposal):
    assert len(proposal["parts"]) == 16
    assert len({p["part_id"] for p in proposal["parts"]}) == 16
    assert proposal["total_witnesses"] == 960 and proposal["total_policy_batches"] == 73
    for part in proposal["parts"]:
        assert part["nominal_source_geometry_preserved"]
        assert part["proposed_specification"]["outputs"] == [part["feature_id"]]
        assert all(0 < len(b["witnesses"]) <= 32 for b in part["policy_batches"])
        assert (
            part["material_assignment"]
            is part["mesh_intent_approval"]
            is part["reviewer"]
            is None
        )


def test_every_measurement_is_source_bound_with_proposed_not_approved_limits(proposal):
    for part in proposal["parts"]:
        probes = [w for b in part["policy_batches"] for w in b["witnesses"]]
        assert len({p["id"] for p in probes}) == len(probes)
        for p in probes:
            assert p["source_boundary_residual_m"] <= 1e-6
            assert (
                p["proposed_minimum_m"] < p["nominal_span_m"] < p["proposed_maximum_m"]
            )
            assert p["status"] == "DRAFT_NUMERICAL_BUDGET_NOT_APPROVED"


def test_cooling_coverage_includes_all_channels_zones_and_five_distinct_measurement_classes(
    proposal,
):
    part = next(
        p for p in proposal["parts"] if p["part_id"] == "illustrative-sector-cooling"
    )
    assert part["witness_count"] == 150
    assert len(part["coverage_sites_local_x_m"]) == 5
    assert len(part["policy_batches"]) == 5
    ribs = next(b for b in part["policy_batches"] if b["id"].startswith("rib-endpoint"))
    assert all("NOT_MATERIAL_THICKNESS" in w["semantics"] for w in ribs["witnesses"])


def test_three_grid_capacity_estimate_is_not_advertised_as_execution_or_accuracy(
    proposal,
):
    for p in proposal["parts"]:
        s = p["three_grid_screen"]
        assert s["spacing_m"][0] > s["spacing_m"][1] > s["spacing_m"][2]
        assert max(s["projected_triangles_with_25_percent_margin"]) <= 4_000_000
        assert s["accuracy_feasibility"].startswith("NOT_ESTABLISHED")
        assert s["projection_status"].endswith("NOT_A_BOUND")


def test_changed_or_substituted_capture_is_refused(tmp_path):
    root = ROOT / "output/picogk-components-2026-10-24/final-generation-evidence"
    original = root / "captured-inputs.json"
    changed = tmp_path / "capture.json"
    changed.write_bytes(original.read_bytes() + b"\n")
    for path, checksum in ((changed, CAPTURE_SHA), (original, "0" * 64)):
        with pytest.raises(ValueError):
            prepare(path, root / "summary.json", checksum)


def test_missing_part_in_baseline_is_not_silently_dropped(tmp_path):
    root = ROOT / "output/picogk-components-2026-10-24/final-generation-evidence"
    baseline = json.loads((root / "summary.json").read_bytes())
    baseline["worker_observations"]["parts"].pop()
    file = tmp_path / "baseline.json"
    file.write_text(json.dumps(baseline))
    with pytest.raises(ValueError):
        prepare(root / "captured-inputs.json", file, CAPTURE_SHA)
