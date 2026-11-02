"""Analytic local sensitivity and exact engine-derived P06 contract tests."""

from dataclasses import replace
from hashlib import sha256

import pytest

from core.exceptions import CosmosError, InvalidInputError
from systems.contracts.geometry import DesignSnapshot, GeometryFeatureGraph
from systems.contracts.results import CalculationResult, ResultStatus
from systems.cycle.operating_sensitivity import study, validate
from systems.geometry.engine_intent import prepare
from tests.fixtures.coupled_cycle import design
from tests.fixtures.engineering_extensions import intent, sensitivity
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


def analytic(_design, spec):
    x = spec["feeds"]["fuel"]["tank_pressure"]["value"]
    return CalculationResult(calculation_type="synthetic", outputs={"solved_candidate_usable": True, "candidate": {"core": {"thrust_n": (x / 1e6) ** 3}}})


def test_cubic_centered_derivative_refines_fourfold_and_originals_unchanged():
    baseline = design(cooling=True)
    original = baseline.to_canonical_json()
    spec = sensitivity()
    out = study(baseline, spec, evaluator=analytic).outputs
    expected = 3 * 4 ** 2 / 1e6
    errors = [abs(row["value"] - expected) for row in out["derivatives"]]
    assert errors[0] / errors[1] == pytest.approx(4, rel=1e-5)
    assert out["study_status"] == "COMPLETED" and len(out["evaluations"]) == 5
    assert out["uncertainty"] == "NOT_QUANTIFIED" and not out["workflow_cycle_complete"]
    assert baseline.to_canonical_json() == original
    assert out["evaluations"][0]["specification"] == spec["recipe"]


def test_invalid_stencil_retained_without_one_sided_or_zero_fallback():
    def invalid(baseline, spec):
        if spec["feeds"]["fuel"]["tank_pressure"]["value"] > 4e6:
            raise InvalidInputError("Synthetic forbidden domain")
        return analytic(baseline, spec)
    out = study(design(cooling=True), sensitivity(), evaluator=invalid).outputs
    assert out["study_status"] == "COMPLETED_WITH_INVALID_DOMAINS"
    assert all(row["value"] is None for row in out["derivatives"])
    assert out["samples"][-1]["output"] is None
    assert len(out["evaluations"]) == 5


def test_budget_exhaustion_stops_new_admission_without_dropping_originals():
    ticks = iter([0, 121, 122, 123, 124, 125])
    out = study(design(cooling=True), sensitivity(), evaluator=analytic, clock=lambda: next(ticks)).outputs
    assert len(out["evaluations"]) == 5
    assert all("budget exhausted" in row["error"]["message"] for row in out["evaluations"])


@pytest.mark.parametrize("bad", ["unit", "values", "recipe", "step", "flag", "source", "parameter"])
def test_bad_contracts_refused(bad):
    spec = sensitivity()
    if bad == "unit": spec["unit"] = "bar"
    if bad == "values": spec["values"] = [4e6] * 3
    if bad == "recipe": spec["recipe"]["cycle_type"] = "EXPANDER"
    if bad == "step": spec["step"]["value"] = True
    if bad == "source": spec["source"] = ""
    if bad == "flag": spec["independent_acceptance"] = True
    if bad == "parameter": spec["parameter"] = "unknowns.chamber_pressure.initial"
    with pytest.raises(CosmosError): validate(spec)


def test_nozzle_intent_uses_exact_source_and_roundtrips_existing_dtos():
    baseline = design(cooling=True)
    original = baseline.to_canonical_json()
    out = prepare(baseline, intent()).outputs
    snapshot = DesignSnapshot.from_json(out["snapshot_json"])
    graph = GeometryFeatureGraph.from_json(out["graph_json"])
    graph.validate_snapshot(snapshot)
    assert snapshot.snapshot_id == out["snapshot_id"]
    assert snapshot.project_id == "engine-design-" + baseline.design_id
    assert snapshot.source_refs[0].source_sha256 == sha256(original.encode()).hexdigest()
    assert graph.topological_order() == ("inner-profile", "wall-profile", "nozzle-wall")
    rows = baseline.workflow.current_result("nozzle").outputs["stations"]
    assert [(r["x_m"], r["inner_radius_m"]) for r in out["profile"]] == [(r["x_m"], r["radius_m"]) for r in rows]
    assert out["engineering_export_eligible"] is False and out["artifacts"] == []
    assert out["backend"] is None and out["intent_status"] == "CAPTURED_NOT_BUILT"
    assert baseline.to_canonical_json() == original
    # The existing DAG computes reversible dependency impacts without native builds.
    wall = next(p for p in snapshot.parameters_si if p.name == "radial-wall-thickness")
    changed = replace(snapshot, parameters_si=tuple(replace(p, value_si=wall.value_si * 2) if p.name == wall.name else p for p in snapshot.parameters_si))
    assert graph.impact(snapshot, changed).stale_features == ("wall-profile", "nozzle-wall")


def test_nozzle_missing_stale_invalid_frame_and_unresolvable_wall_refused():
    baseline = design(cooling=True)
    for key, value in (("frame", "invented-left-handed"), ("source_tolerance", {"value": .002, "unit": "m"}), ("wall_thickness", {"value": .002, "unit": "mm"})):
        spec = intent(); spec[key] = value
        with pytest.raises(InvalidInputError): prepare(baseline, spec)
    baseline.workflow.graph.get("nozzle").status = ResultStatus.STALE
    with pytest.raises(InvalidInputError): prepare(baseline, intent())


def test_geometry_intent_does_not_enter_fixture_only_native_authority():
    from systems.geometry.workbench import GeometryWorkbench
    with pytest.raises(ValueError):
        GeometryWorkbench.revision({"operation": "revolve_x_intent", "backend": "occt", "voxel_m": .001})
