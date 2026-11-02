"""Small deterministic geometry checks; not R08 or hardware qualification."""

import copy
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from systems.contracts.geometry import GeometryContractError
from systems.geometry.component_model import compile_model
from systems.geometry.component_reference import PartReference
from systems.geometry.engine_redesign import compile_candidate, suggest


@pytest.fixture
def source_plan():
    # Frozen research geometry copied from the retained 2026-10-24 input.
    # No dependency on output/, a live project, native kernels or measurements.
    specification = json.loads(
        (Path(__file__).parents[2] / "fixtures/compact_engine_source.json").read_text()
    )
    return compile_model(
        specification,
        "engine-component-compact-test",
        "software-only",
        "2026-10-28T00:00:00+00:00",
    )


def test_source_seed_preserves_16_parts_and_produces_six_groups(source_plan):
    before = source_plan.snapshot.to_json()
    seed = suggest(source_plan)
    candidate = compile_candidate(source_plan, seed)
    report = candidate.report()
    assert report["source_metal_parts"] == 16
    assert report["candidate_metal_groups"] == 6
    assert report["channel_count"] == 6
    assert len(seed["return_part_ids"]) == 9
    assert source_plan.snapshot.to_json() == before
    assert report["native_topology"] == "NOT_BUILT"
    assert report["thermal_mapping"] == "REQUIRES_MATCHED_VARIABLE_SECTOR_MODEL"
    assert candidate.wire() == compile_candidate(source_plan, seed).wire()
    total_source = sum(
        PartReference(source_plan, p).volume_m3 for p in source_plan.parts
    )
    assert sum(
        g["reference_volume_m3"] for g in candidate.wire()["groups"]
    ) == pytest.approx(total_source, rel=1e-12)


def test_variable_depth_is_actual_cut_geometry_not_only_metadata(source_plan):
    seed = suggest(source_plan)
    first = compile_candidate(source_plan, seed)
    seed["stations"][12]["depth"]["value"] *= 0.8
    second = compile_candidate(source_plan, seed)
    assert second.channels[0].profile[12][2] < first.channels[0].profile[12][2]
    assert (
        second.report()["total_channel_volume_m3"]
        < first.report()["total_channel_volume_m3"]
    )
    assert second.wire()["recipe_sha256"] != first.wire()["recipe_sha256"]
    assert second.groups[0].add[0].profile == first.groups[0].add[0].profile
    assert second.channels[0].profile[0] == first.channels[0].profile[0]
    assert second.channels[0].profile[-1] == first.channels[0].profile[-1]
    seed["stations"][12]["depth"]["value"] = 100
    assert second.specification["stations"][12]["depth"]["value"] != 100


@pytest.mark.parametrize(
    "mutation",
    [
        lambda s: s.update(channel_family="helical"),
        lambda s: s.update(extra=True),
        lambda s: s["stations"].pop(),
        lambda s: s["stations"][0]["depth"].update(value=0.002),
        lambda s: s["stations"][1]["x"].update(value=0),
        lambda s: s["stations"][1]["depth"].update(value=1),
        lambda s: s["stations"][1]["depth"].update(value=float("nan")),
        lambda s: s["stations"][1]["depth"].update(value=True),
        lambda s: s["stations"][1]["depth"].update(unit="mm"),
        lambda s: s["return_part_ids"].pop(),
        lambda s: s["return_part_ids"].append(s["return_part_ids"][0]),
        lambda s: s.update(header_part_ids=["fuel-supply", "oxidizer-supply"]),
    ],
)
def test_rejects_unsafe_or_unsupported_drafts(source_plan, mutation):
    seed = copy.deepcopy(suggest(source_plan))
    mutation(seed)
    with pytest.raises(GeometryContractError):
        compile_candidate(source_plan, seed)


def test_disconnected_return_rejected_even_when_ids_exist(source_plan):
    parts = tuple(
        replace(p, frame_id="world") if p.part_id == "return-over-flange" else p
        for p in source_plan.parts
    )
    altered = replace(source_plan, parts=parts)
    with pytest.raises(GeometryContractError):
        compile_candidate(altered, suggest(source_plan))


def test_channel_integral_matches_independent_piecewise_formula(source_plan):
    candidate = compile_candidate(source_plan, suggest(source_plan))
    rows = np.array(candidate.channels[0].profile)
    x, low, high = rows.T
    expected = np.sum(
        np.diff(x)
        / 3
        * (
            high[:-1] ** 2
            + high[:-1] * high[1:]
            + high[1:] ** 2
            - low[:-1] ** 2
            - low[:-1] * low[1:]
            - low[1:] ** 2
        )
    )
    expected *= candidate.channels[0].sector[1] / 2 * len(candidate.channels)
    assert candidate.report()["total_channel_volume_m3"] == pytest.approx(
        expected, rel=1e-12
    )
