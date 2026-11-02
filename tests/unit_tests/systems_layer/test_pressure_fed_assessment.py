"""Real API baseline, synthetic feed assumptions, no hardware evidence."""

from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256

import pytest

from api.pressure_fed import assess_pressure_fed
from api.propulsion_workflow import (
    create_design,
    run_phase3,
    update_cycle,
    update_propellants,
    update_requirements,
)
from core.exceptions import InvalidInputError
from physics.exceptions import InsufficientDataError, OutOfRangeError
from systems.contracts.results import ResultStatus
from systems.cycle.pressure_fed import INPUT_SCHEMA


def value(magnitude, unit):
    return {"value": magnitude, "unit": unit}


@pytest.fixture(autouse=True)
def isolated_catalog(monkeypatch):
    # Core isolation can unload Physics while API functions retain an earlier
    # registry namespace. Isolate both, as in the existing sensitivity tests.
    from api import catalogs
    from physics.thermochemistry import propellants

    namespaces = {
        id(f.__globals__): f.__globals__
        for f in (propellants.registry_size, catalogs.registry_size)
    }
    for namespace in namespaces.values():
        monkeypatch.setitem(namespace, "_PROPELLANT_REGISTRY", {})
        monkeypatch.setitem(namespace, "_ALIAS_REGISTRY", {})
        namespace["load_json_database"](catalogs.PROPELLANT_CANDIDATE_DB)


@pytest.fixture
def baseline():
    design = create_design(name="Pressure-fed software verification only")
    update_cycle(design, "PRESSURE_FED")
    update_requirements(
        design,
        {
            "target_chamber_pressure": 5e6,
            "target_thrust": 10000,
            "ambient_pressure": 0.0,
            "expansion_ratio": 10.0,
            "mixture_ratio": 2.0,
        },
    )
    update_propellants(design, oxidizer_id="LOX", fuel_id="RP1", mixture_ratio=2.0)
    assert run_phase3(
        design,
        chamber_temperature_k=3000.0,
        gamma=1.2,
        molecular_weight_kg_per_mol=0.022,
        throat_area_m2=0.001,
        expansion_ratio=10.0,
    )["ok"]
    return design


def specification(design):
    total = design.workflow.results["performance"].outputs["mass_flow"]["magnitude"]
    # Independent test construction fixes velocity at2m/s and uses the
    # predeclared hand-calculated +182000Pa pressure budget for each stream.
    flows = {"oxidizer": 2 * total / 3, "fuel": total / 3}
    return {
        "schema": INPUT_SCHEMA,
        "regime": "STEADY_SINGLE_PHASE_INCOMPRESSIBLE",
        "pressurant_boundary": "REGULATED_TANK_PRESSURE",
        "flow_accounting": "CORE_ONLY_NO_DIVERSION",
        "gravity": value(10, "m/s2"),
        "pressure_tolerance": value(1e-6, "Pa"),
        "mass_flow_tolerance": value(1e-12, "kg/s"),
        "external_oxidizer_outflow": value(0, "kg/s"),
        "external_fuel_outflow": value(0, "kg/s"),
        "streams": {
            name: {
                "phase": "LIQUID",
                "temperature": value(90 if name == "oxidizer" else 290, "K"),
                "density": value(1000, "kg/m3"),
                "density_source": "Synthetic constant for balance verification, not measured propellant data",
                "tank_pressure": value(5182000, "Pa"),
                "tank_pressure_source": "Synthetic imposed absolute tank boundary",
                "tank_mass_flow": value(flow, "kg/s"),
                "tank_mass_flow_source": "Synthetic independently specified withdrawal",
                "manifold_area": value(flow / 2000, "m2"),
                "elevation_rise": value(3, "m"),
                "injector_static_pressure_drop": value(100000, "Pa"),
                "injector_source": "Synthetic Pc-to-manifold STATIC delta-p, not upstream energy loss",
                "losses": {
                    label: {
                        "pressure_equivalent": value(drop, "Pa"),
                        "source": "Synthetic irreversible upstream loss at declared flow and temperature; no injector double count",
                    }
                    for label, drop in (
                        ("feed_line", 20000),
                        ("valves", 30000),
                        ("cooling", 0),
                    )
                },
            }
            for name, flow in flows.items()
        },
    }


def test_exact_baseline_read_only_source_identity_and_independent_balances(baseline):
    spec = specification(baseline)
    before = baseline.to_canonical_json()
    original_spec = deepcopy(spec)
    envelope = assess_pressure_fed(baseline, spec)
    result = envelope["result"]
    assert baseline.to_canonical_json() == before and spec == original_spec
    assert result["inputs"]["baseline_canonical_text"] == before
    assert result["inputs"]["baseline_sha256"] == sha256(before.encode()).hexdigest()
    assert result["inputs"]["specification"] == spec
    assert result["stage_id"] is None
    assert result["outputs"]["assessment_balances_closed_within_declared_tolerances"]
    for row in result["outputs"]["streams"].values():
        assert row["required_source_pressure_pa"] == pytest.approx(5182000, abs=1e-9)
        assert (
            row["required_sink_pressure_pa"] == 5100000
        )  # static injector dp counted once
        assert row["irreversible_loss_pa"] == 50000
        assert row["outlet_velocity_m_s"] == pytest.approx(2, abs=1e-12)
        assert row["pressure_residual_pa"] == pytest.approx(0, abs=1e-9)
        assert row["mass_residual_kg_s"] == pytest.approx(0, abs=1e-14)
    for stage, original in result["inputs"]["source_results"].items():
        assert original == json.loads(before)["workflow"]["results"][stage]
    assert baseline.cycle_configuration.implementation_status.value == "PARTIAL"
    assert (
        baseline.workflow.graph.get("cycle").implementation_status.value
        == "PARTIAL"
    )
    assert result["outputs"]["workflow_cycle_complete"] is False
    assert result["outputs"]["physical_validation"] == "NOT_PERFORMED"
    assert result["outputs"]["shaft_power"] == {
        "status": "NOT_APPLICABLE",
        "value": None,
        "unit": "W",
    }
    assert result["validation"]["status"] == "NOT_PERFORMED"
    assert all(len(digest) == 64 for digest in envelope["method_sources"].values())
    result["inputs"]["specification"]["streams"]["fuel"]["density"]["value"] = 1
    assert spec == original_spec  # no returned nested aliases into request


@pytest.mark.parametrize(
    "difference,state", [(-1000, "DEFICIT"), (1000, "SURPLUS_REQUIRES_CONTROL")]
)
def test_pressure_imbalance_is_not_flow_solution_or_closure(
    baseline, difference, state
):
    spec = specification(baseline)
    spec["streams"]["fuel"]["tank_pressure"]["value"] += difference
    out = assess_pressure_fed(baseline, spec)["result"]["outputs"]
    assert out["streams"]["fuel"]["pressure_state"] == state
    assert not out["assessment_balances_closed_within_declared_tolerances"]
    assert out["flow_solution"] == "NOT_SOLVED_IMPOSED_CORE_FLOW"


def test_independent_stream_mass_errors_cannot_cancel_to_false_closure(baseline):
    spec = specification(baseline)
    spec["streams"]["oxidizer"]["tank_mass_flow"]["value"] += 0.1
    spec["streams"]["fuel"]["tank_mass_flow"]["value"] -= 0.1
    out = assess_pressure_fed(baseline, spec)["result"]["outputs"]
    assert out["total_mass_residual_kg_s"] == pytest.approx(0, abs=1e-14)
    assert out["streams"]["oxidizer"]["mass_residual_kg_s"] == pytest.approx(
        0.1, abs=1e-14
    )
    assert out["streams"]["fuel"]["mass_residual_kg_s"] == pytest.approx(
        -0.1, abs=1e-14
    )
    assert not out["assessment_balances_closed_within_declared_tolerances"]


@pytest.mark.parametrize(
    "stage", ["operating_point", "propellants", "thermochemistry", "performance"]
)
@pytest.mark.parametrize("where", ["result", "graph", "missing"])
def test_missing_or_stale_sources_refuse_without_mutation(baseline, stage, where):
    spec = specification(baseline)
    if where == "result":
        baseline.workflow.results[stage].status = ResultStatus.STALE
    elif where == "graph":
        baseline.workflow.graph.get(stage).status = ResultStatus.STALE
    else:
        del baseline.workflow.results[stage]
    before = baseline.to_canonical_json()
    with pytest.raises(InsufficientDataError):
        assess_pressure_fed(baseline, spec)
    assert baseline.to_canonical_json() == before


@pytest.mark.parametrize(
    "cycle",
    ["UNSPECIFIED", "GAS_GENERATOR", "STAGED_COMBUSTION", "EXPANDER", "ELECTRIC_PUMP"],
)
def test_unsupported_or_unselected_cycle_refused(baseline, cycle):
    spec = specification(baseline)
    update_cycle(baseline, cycle)
    with pytest.raises(OutOfRangeError):
        assess_pressure_fed(baseline, spec)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("schema", "v0"),
        ("regime", "TWO_PHASE"),
        ("pressurant_boundary", "BLOWDOWN"),
        ("flow_accounting", "INFER_DIVERSION"),
        ("gravity", value(True, "m/s2")),
        ("pressure_tolerance", value(0, "Pa")),
        ("mass_flow_tolerance", value(-1, "kg/s")),
        ("external_fuel_outflow", value(0.01, "kg/s")),
        ("external_oxidizer_outflow", value(0.01, "kg/s")),
        ("gravity", value(9.81, "g")),
        ("pressure_tolerance", value(float("nan"), "Pa")),
        ("gravity", value(float("inf"), "m/s2")),
        ("gravity", value(10**400, "m/s2")),
    ],
)
def test_strict_top_level_input_and_no_silent_diversion(baseline, field, bad):
    spec = specification(baseline)
    spec[field] = bad
    with pytest.raises((InvalidInputError, OutOfRangeError)):
        assess_pressure_fed(baseline, spec)


@pytest.mark.parametrize(
    "path,action",
    [
        ((), "extra"),
        ((), "delete"),
        (("streams",), "extra"),
        (("streams", "fuel"), "extra"),
        (("streams", "fuel", "density"), "extra"),
        (("streams", "fuel", "losses"), "extra"),
        (("streams", "fuel", "losses"), "delete"),
        (("streams", "fuel", "losses", "valves"), "extra"),
    ],
)
def test_missing_and_extra_nested_fields_are_not_ignored(baseline, path, action):
    spec = specification(baseline)
    node = spec
    for part in path:
        node = node[part]
    if action == "extra":
        node["ignored"] = 1
    else:
        node.pop(next(iter(node)))
    with pytest.raises(InvalidInputError):
        assess_pressure_fed(baseline, spec)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("phase", "GAS"),
        ("temperature", value(0, "K")),
        ("density", value(1000, "g/cm3")),
        ("tank_pressure", value(True, "Pa")),
        ("manifold_area", value(0, "m2")),
        ("injector_static_pressure_drop", value(0, "Pa")),
        ("density_source", ""),
        ("tank_pressure_source", " " * 20),
        ("injector_source", "a" * 2049),
    ],
)
def test_stream_phase_units_sources_and_signs_are_explicit(baseline, field, bad):
    spec = specification(baseline)
    spec["streams"]["fuel"][field] = bad
    with pytest.raises((InvalidInputError, InsufficientDataError, OutOfRangeError)):
        assess_pressure_fed(baseline, spec)


@pytest.mark.parametrize("mode", ["configuration", "thermo_result"])
def test_cea_is_not_silently_assumed(baseline, mode):
    spec = specification(baseline)
    if mode == "configuration":
        baseline.thermochemistry_configuration["mode"] = "nasa_cea"
    else:
        baseline.workflow.results["thermochemistry"].inputs["engine"] = "nasa/cea"
    with pytest.raises(OutOfRangeError):
        assess_pressure_fed(baseline, spec)


def test_no_consumption_or_mutation_of_existing_subsystem_results(baseline):
    spec = specification(baseline)
    from systems.contracts.results import CalculationResult

    baseline.workflow.results["cooling"] = CalculationResult(
        calculation_type="synthetic-unclosed-cooling",
        status=ResultStatus.CURRENT,
        outputs={"unknown_diversion": True},
    )
    before = baseline.to_canonical_json()
    out = assess_pressure_fed(baseline, spec)["result"]
    assert "cooling" not in out["inputs"]["source_results"]
    assert "NOT_ASSESSED" in out["outputs"]["subsystem_coupling"]
    assert baseline.to_canonical_json() == before


def test_inconsistent_retained_pressure_refuses(baseline):
    spec = specification(baseline)
    baseline.workflow.results["performance"].inputs["chamber_pressure"]["magnitude"] = (
        6e6
    )
    with pytest.raises(InvalidInputError, match="disagree"):
        assess_pressure_fed(baseline, spec)


@pytest.mark.parametrize(
    "location,key,bad",
    [
        ("propellant_configuration", "fuel_id", "hydrazine"),
        ("requirements", "mixture_ratio", 4),
        ("requirements", "cycle_type", "UNSPECIFIED"),
        ("operating_point", "mixture_ratio", 4),
    ],
)
def test_inconsistent_current_fields_cannot_relabel_retained_result(
    baseline, location, key, bad
):
    spec = specification(baseline)
    setattr(getattr(baseline, location), key, bad)
    with pytest.raises(InvalidInputError, match="inconsistent"):
        assess_pressure_fed(baseline, spec)


@pytest.mark.parametrize(
    "path,bad",
    [
        (("inputs", "chamber_pressure", "magnitude"), True),
        (("outputs", "mass_flow", "magnitude"), -1),
    ],
)
def test_malformed_retained_quantities_are_not_coerced_to_answers(baseline, path, bad):
    spec = specification(baseline)
    node = getattr(baseline.workflow.results["performance"], path[0])
    node[path[1]][path[2]] = bad
    with pytest.raises(InvalidInputError):
        assess_pressure_fed(baseline, spec)


def test_current_propellant_result_ratio_mismatch_refuses(baseline):
    spec = specification(baseline)
    baseline.workflow.results["propellants"].outputs["mixture_ratio"]["value"] = 4
    with pytest.raises(InvalidInputError, match="inconsistent"):
        assess_pressure_fed(baseline, spec)


@pytest.mark.parametrize("moment", ["before", "during"])
def test_method_source_drift_refuses_public_result(baseline, monkeypatch, moment):
    from api import pressure_fed

    original = pressure_fed._methods
    calls = 0

    def changed():
        nonlocal calls
        calls += 1
        return {"changed": "0" * 64} if moment == "before" or calls > 1 else original()

    monkeypatch.setattr(pressure_fed, "_methods", changed)
    before = baseline.to_canonical_json()
    with pytest.raises(InvalidInputError, match="sources changed"):
        assess_pressure_fed(baseline, specification(baseline))
    assert baseline.to_canonical_json() == before
