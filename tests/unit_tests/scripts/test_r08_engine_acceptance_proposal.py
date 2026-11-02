"""Offline planning checks; these are NOT additional native engine qualification."""

import json
import os
from hashlib import sha256
from pathlib import Path

import pytest

from scripts import prepare_r08_engine_acceptance_proposal as proposal_script
from systems.geometry.component_model import compile_model
from systems.geometry.qualification_policy import validate
from tests.fixtures.component_geometry import model


@pytest.fixture
def manufactured_inputs(tmp_path):
    """Fabricated software inputs, with no saved engine or native-run evidence."""
    specification = model("cooling.axial_sector", fluids=False)
    specification["features"][-1]["parameters"]["count"]["value"] = 8
    pipe = model("pipe.circular")["features"][0]
    pipe["id"] = "sample-pipe"
    specification["features"].append(pipe)
    specification["outputs"].append("sample-pipe")
    plan = compile_model(
        specification,
        "engine-component-manufactured-proposal-test",
        "software-fixture-only",
        "2026-10-20T00:00:00+00:00",
    )
    canonical = json.dumps(
        {
            "specification": specification,
            "snapshot_json": plan.snapshot.to_json(),
            "graph_json": plan.graph.to_json(),
        },
        sort_keys=True,
    )
    capture, baseline = tmp_path / "capture.json", tmp_path / "baseline.json"
    capture.write_text(
        json.dumps(
            {
                "model_canonical_json": canonical,
                "model_sha256": sha256(canonical.encode()).hexdigest(),
                "model_commit_id": "manufactured-software-fixture-only",
            }
        )
    )
    checksum = sha256(capture.read_bytes()).hexdigest()
    baseline.write_text(
        json.dumps(
            {
                "test_only": "Fabricated counts; no native campaign was executed",
                "inputs_sha256": checksum,
                "software_qa_pass": True,
                "worker_observations": {
                    "actual_voxel_m": 0.00008,
                    "parts": [
                        {"part_id": part.part_id, "triangle_count": 100}
                        for part in plan.parts
                    ],
                },
            }
        )
    )
    return capture, baseline, checksum


@pytest.fixture(params=("manufactured", "local-engine"))
def proposal_inputs(request, manufactured_inputs, monkeypatch):
    if request.param == "local-engine":
        evidence_root = os.environ.get("COSMOS_R08_ENGINE_EVIDENCE_ROOT")
        if not evidence_root:
            pytest.skip("Saved engine checks require COSMOS_R08_ENGINE_EVIDENCE_ROOT")
        root = Path(evidence_root)
        return (
            root / "captured-inputs.json",
            root / "summary.json",
            proposal_script.CAPTURE_SHA,
            (16, 960, 73, "illustrative-sector-cooling", 150, 5),
        )
    capture, baseline, checksum = manufactured_inputs
    # This test-only identity admits only these fabricated bytes. The production
    # exact-engine checksum and all production admission checks remain unchanged.
    monkeypatch.setattr(proposal_script, "CAPTURE_SHA", checksum)
    return capture, baseline, checksum, (2, 219, 13, "channels", 200, 10)


@pytest.fixture
def proposal(proposal_inputs):
    capture, baseline, checksum, _ = proposal_inputs
    before = [sha256(p.read_bytes()).hexdigest() for p in (capture, baseline)]
    result = proposal_script.prepare(capture, baseline, checksum)
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


def test_all_exact_source_parts_are_preserved_and_every_batch_is_bounded(
    proposal, proposal_inputs,
):
    part_count, witnesses, batches, *_ = proposal_inputs[3]
    assert len(proposal["parts"]) == part_count
    assert len({p["part_id"] for p in proposal["parts"]}) == part_count
    assert proposal["total_witnesses"] == witnesses
    assert proposal["total_policy_batches"] == batches
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
    proposal, proposal_inputs,
):
    _, _, _, part_id, witnesses, batches = proposal_inputs[3]
    part = next(
        p for p in proposal["parts"] if p["part_id"] == part_id
    )
    assert part["witness_count"] == witnesses
    assert len(part["coverage_sites_local_x_m"]) == 5
    assert len(part["policy_batches"]) == batches
    probes = [w for b in part["policy_batches"] for w in b["witnesses"]]
    assert len({w["category"] for w in probes}) == 5
    ribs = [w for w in probes if w["category"] == "rib-endpoint-chord"]
    assert ribs and all("NOT_MATERIAL_THICKNESS" in w["semantics"] for w in ribs)


def test_three_grid_capacity_estimate_is_not_advertised_as_execution_or_accuracy(
    proposal,
):
    for p in proposal["parts"]:
        s = p["three_grid_screen"]
        assert s["spacing_m"][0] > s["spacing_m"][1] > s["spacing_m"][2]
        assert max(s["projected_triangles_with_25_percent_margin"]) <= 4_000_000
        assert s["accuracy_feasibility"].startswith("NOT_ESTABLISHED")
        assert s["projection_status"].endswith("NOT_A_BOUND")


def test_changed_or_substituted_capture_is_refused(tmp_path, proposal_inputs):
    original, baseline, checksum, _ = proposal_inputs
    changed = tmp_path / "changed-capture.json"
    changed.write_bytes(original.read_bytes() + b"\n")
    for path, expected in ((changed, checksum), (original, "0" * 64)):
        with pytest.raises(ValueError, match="Exact bounded immutable engine capture"):
            proposal_script.prepare(path, baseline, expected)


def test_missing_part_in_baseline_is_not_silently_dropped(tmp_path, proposal_inputs):
    capture, original_baseline, checksum, _ = proposal_inputs
    baseline = json.loads(original_baseline.read_bytes())
    baseline["worker_observations"]["parts"].pop()
    file = tmp_path / "missing-part-baseline.json"
    file.write_text(json.dumps(baseline))
    with pytest.raises(ValueError, match="No omitted or extra source parts"):
        proposal_script.prepare(capture, file, checksum)


def test_manufactured_capture_is_not_admitted_as_the_saved_engine(manufactured_inputs):
    capture, baseline, checksum = manufactured_inputs
    assert checksum != proposal_script.CAPTURE_SHA
    with pytest.raises(ValueError, match="Exact bounded immutable engine capture"):
        proposal_script.prepare(capture, baseline, checksum)
