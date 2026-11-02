"""Manufactured readiness checks, not thermal/engine validation evidence."""

import copy
import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from systems.contracts.geometry import SourceReference
from systems.geometry.compact_analysis import assess_readiness, record_sha256
from systems.geometry.component_model import compile_model
from systems.geometry.engine_redesign import compile_candidate, suggest
from tests.unit_tests.physics.test_heated_liquid_segment import table


@pytest.fixture
def inputs():
    specification = json.loads(
        (Path(__file__).parents[2] / "fixtures/compact_engine_source.json").read_text()
    )
    plan = compile_model(
        specification,
        "engine-component-compact-analysis-test",
        "manufactured-only",
        "2026-10-30T00:00:00+00:00",
        sources=(
            SourceReference(
                "engine-baseline", "propulsion/software-fixture.json", "b" * 64
            ),
        ),
    )
    candidate = compile_candidate(plan, suggest(plan))
    liquid = json.loads(json.dumps(asdict(table())))
    material = [
        {
            "curve": {
                "material_id": "SYNTHETIC",
                "condition": "Manufactured response only",
                "temperatures_k": [298.15, 810.95],
                "conductivities_w_m_k": [323, 303],
                "source": "Manufactured domain fixture, not an engine material",
                "source_sha256": "c" * 64,
            },
            "condition": {"alloy_id": "SYNTHETIC", "process": None},
        }
    ]
    identity = {
        "baseline_sha256": "b" * 64,
        "baseline_commit_id": "software-baseline",
        "component_source_commit_id": "software-component",
        "recipe_sha256": candidate.wire()["recipe_sha256"],
        "liquid_table_sha256": record_sha256(liquid),
        "material_records_sha256": record_sha256(material),
    }
    return candidate, {
        "liquid_record": liquid,
        "material_records": material,
        "physics_identity": identity,
    }


def codes(result):
    return {item["code"] for item in result["blockers"]}


def test_exact_geometry_and_domains_never_fabricate_solved_state(inputs):
    candidate, values = inputs
    before = candidate.wire(), copy.deepcopy(values)
    result = assess_readiness(candidate, **values)
    assert result["status"] == "BLOCKED"
    assert not result["matched_thermal_feed_solved"]
    assert all(value is None for value in result["solution"].values())
    assert result["geometry"]["channel_count"] == 6
    assert result["geometry"]["stations"] == candidate.report()["stations"]
    assert result["geometry"]["return_route"]["source_primitive_count"] == 9
    assert result["geometry"]["return_route"]["centerline_length_m"] > 0
    assert result["geometry"]["section_basis"] == "AXIAL_APERTURES_NOT_FLOW_NORMAL"
    assert "NO_WALL_LIQUID_DOMAIN_OVERLAP" in codes(result)
    assert "MATERIAL_CONDITION_UNRESOLVED" in codes(result)
    assert result["physical_validation"] == "NOT_PERFORMED"
    assert (candidate.wire(), values) == before
    json.dumps(result, allow_nan=False)


def test_absent_candidate_and_physics_source_fail_closed(inputs):
    candidate, values = inputs
    assert codes(assess_readiness(None, **values)) == {"CANDIDATE_SOURCE_MISSING"}
    assert "PHYSICS_IDENTITY_MISSING" in codes(assess_readiness(candidate))
    changed = copy.deepcopy(values)
    changed["physics_identity"]["baseline_sha256"] = "d" * 64
    assert "PHYSICS_SOURCE_MISMATCH" in codes(assess_readiness(candidate, **changed))
    changed["physics_identity"]["baseline_sha256"] = "b" * 64
    changed["physics_identity"]["recipe_sha256"] = "d" * 64
    assert "PHYSICS_SOURCE_MISMATCH" in codes(assess_readiness(candidate, **changed))


def test_altered_operands_cannot_reuse_the_original_recipe(inputs):
    candidate, values = inputs
    changed = replace(candidate, channels=candidate.channels[:-1])
    assert "CANDIDATE_SOURCE_CHANGED" in codes(assess_readiness(changed, **values))


@pytest.mark.parametrize(
    "record,key,code",
    [
        ("liquid_record", "source", "LIQUID_SOURCE_CHANGED"),
        ("material_records", "source", "MATERIAL_SOURCE_CHANGED"),
    ],
)
def test_changed_pinned_source_record_is_reported(inputs, record, key, code):
    candidate, values = inputs
    values = copy.deepcopy(values)
    target = values[record] if record == "liquid_record" else values[record][0]["curve"]
    target[key] = "Different supplied source"
    assert code in codes(assess_readiness(candidate, **values))


def test_apparent_overlap_still_cannot_promote_to_a_matched_solve(inputs):
    candidate, values = inputs
    values = copy.deepcopy(values)
    values["material_records"][0]["curve"]["temperatures_k"] = [100, 810.95]
    values["physics_identity"].pop("material_records_sha256")
    result = assess_readiness(candidate, **values)
    assert result["material_domains"][0]["subcooled_contact_domain_overlap"]
    assert "NO_WALL_LIQUID_DOMAIN_OVERLAP" not in codes(result)
    assert "VARIABLE_SECTOR_TRANSFER_UNSUPPORTED" in codes(result)
    assert result["status"] == "BLOCKED" and result["solution"]["heat_w"] is None


def test_invalid_or_missing_fluid_material_and_baseline_rejected(inputs):
    candidate, values = inputs
    missing = assess_readiness(candidate, liquid_record={}, material_records=[])
    assert {"LIQUID_DATA_MISSING_OR_INVALID", "MATERIAL_DATA_MISSING"} <= codes(missing)
    invalid = copy.deepcopy(values)
    invalid["liquid_record"]["states"][0][0]["density_kg_m3"] = float("nan")
    assert "LIQUID_DATA_MISSING_OR_INVALID" in codes(
        assess_readiness(candidate, **invalid)
    )
    without = replace(
        candidate.plan,
        snapshot=replace(
            candidate.plan.snapshot,
            source_refs=tuple(
                ref
                for ref in candidate.plan.snapshot.source_refs
                if ref.ref_id != "engine-baseline"
            ),
        ),
    )
    without = replace(
        without, graph=replace(without.graph, snapshot_id=without.snapshot.snapshot_id)
    )
    changed = compile_candidate(without, candidate.specification)
    values = copy.deepcopy(values)
    values["physics_identity"]["recipe_sha256"] = changed.wire()["recipe_sha256"]
    assert "PHYSICS_SOURCE_MISMATCH" in codes(assess_readiness(changed, **values))
