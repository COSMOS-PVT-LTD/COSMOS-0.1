"""Guided policy/replay and real CEA checks; no physical validation or live data."""

from copy import deepcopy

import pytest

from api.guided_engine import methods
from core.exceptions import InvalidInputError
from plugins.guided_engine import sources
from plugins.nasa_cea import bind_nasa_cea_engine
from systems.guided_engine.evaluate import evaluate
from systems.guided_engine.resolution import digest, resolve


def engine_brief():
    return {
        "thrust": {"value": 1500, "unit": "N"},
        "propellants": {"fuel": "LCH4", "oxidizer": "LOX"},
        "chamber_pressure": {"value": 500000, "unit": "Pa"},
        "environment": {"kind": "SEA_LEVEL_STANDARD"},
        "burn_duration": {"value": 5, "unit": "s"},
        "cycle": "PRESSURE_FED",
    }


def plan(b=None, overrides=None):
    return resolve(b or engine_brief(), overrides or {}, sources.package(), methods())


def calculation(b=None, overrides=None):
    p = plan(b, overrides)
    e = p["effective"]
    adapter = bind_nasa_cea_engine(
        fuel_temperature_k=e["fuel_temperature"]["value"],
        oxidizer_temperature_k=e["oxidizer_temperature"]["value"],
        exit_pressure_pa=p["ambient_pressure_pa"] or 101325,
        require_explicit_temperatures=True,
    )
    return p, *evaluate(p, adapter)


def test_pinned_resolution_is_deterministic_detached_and_all_values_explained():
    b = engine_brief()
    p = plan(b)
    assert p == plan(b)
    assert p["review_hash"] == digest(
        {k: v for k, v in p.items() if k != "review_hash"}
    )
    assert set(p["effective"]) <= {row["key"] for row in p["parameters"]}
    assert all(
        row["uncertainty"] is None and row["basis"] and row["category"]
        for row in p["parameters"]
    )
    b["thrust"]["value"] = 999
    assert p["brief"]["thrust"]["value"] == 1500
    assert p["physical_validation"] == "NOT_PERFORMED"


@pytest.mark.parametrize(
    "value", [True, -1, 0, float("nan"), float("inf"), "1500", None]
)
def test_bad_numbers_refused(value):
    b = engine_brief()
    b["thrust"]["value"] = value
    with pytest.raises(InvalidInputError):
        plan(b)


@pytest.mark.parametrize(
    "field,value",
    [
        ("cycle", "GAS_GENERATOR"),
        ("propellants", {"fuel": "RP1", "oxidizer": "LOX"}),
        ("environment", {"kind": "altitude", "altitude": 500}),
        ("chamber_pressure", {"value": 5, "unit": "bar"}),
    ],
)
def test_unsupported_or_ambiguous_inputs_not_substituted(field, value):
    b = engine_brief()
    b[field] = value
    with pytest.raises(InvalidInputError):
        plan(b)


def test_low_pressure_ratio_rejected_and_explicit_custom_vacuum_accepted():
    b = engine_brief()
    b["chamber_pressure"]["value"] = 200000
    with pytest.raises(InvalidInputError, match="2.5"):
        plan(b)
    b["environment"] = {"kind": "CUSTOM", "pressure": {"value": 0, "unit": "Pa"}}
    b["burn_duration"] = None
    assert plan(b)["ambient_pressure_pa"] == 0


@pytest.mark.parametrize(
    "override",
    [
        {"worker": "malicious"},
        {"injector_holes": {"value": 8.5, "unit": "1"}},
        {"fuel_temperature": {"value": 300, "unit": "K"}},
        {"injector_cd": {"value": 2, "unit": "1"}},
    ],
)
def test_override_whitelist_and_domain(override):
    with pytest.raises(InvalidInputError):
        plan(overrides=override)


def test_override_retains_original_and_new_review_hash():
    baseline = plan()
    changed = plan(overrides={"injector_cd": {"value": 0.6, "unit": "1"}})
    row = next(p for p in changed["parameters"] if p["key"] == "injector_cd")
    assert row["original"]["value"] == 0.7 and row["override"]
    assert changed["review_hash"] != baseline["review_hash"]
    assert baseline["effective"]["injector_cd"]["value"] == 0.7


def test_changed_or_missing_property_package_never_falls_back(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "ROOT", tmp_path)
    with pytest.raises(InvalidInputError, match="missing"):
        sources.package()
    (tmp_path / "fuel-nist-6bar.tsv").write_text("fabricated")
    with pytest.raises(InvalidInputError, match="checksum"):
        sources.package()


def test_uncovered_inlet_state_requires_another_reviewed_profile():
    with pytest.raises(InvalidInputError, match="fuel_temperature"):
        plan(overrides={"fuel_temperature": {"value": 112, "unit": "K"}})


def test_real_cea_target_sizing_and_same_unit_contract_in_expert_design():
    p, design, result = calculation()
    assert result["calculated_thrust_n"] == pytest.approx(1500, rel=2e-4)
    assert result["mass_flow_kg_s"] == pytest.approx(
        result["fuel_flow_kg_s"] + result["oxidizer_flow_kg_s"]
    )
    assert result["mixture_ratio"] == pytest.approx(2.63, abs=0.02)
    assert result["specific_impulse_s"] == pytest.approx(202.5, abs=0.3)
    assert not design.operating_point.gamma_is_assumption
    assert design.workflow.current_result("performance")
    assert design.workflow.current_result("injector")
    assert design.requirements.target_thrust.to_si() == 1500
    assert result["review_hash"] == p["review_hash"]
    assert result["propellant_mass_kg"] == pytest.approx(result["mass_flow_kg_s"] * 5)
    assert not result["engine_complete"]
    assert any(
        s["state"] == "BLOCKED" and "cooling" in s["name"].lower()
        for s in result["stages"]
    )


def test_new_thrust_resizes_consistently_without_claiming_hardware_scaling():
    locked = {"mixture_ratio": {"value": 2.63, "unit": "1"}}
    _, _, a = calculation(overrides=locked)
    b = engine_brief()
    b["thrust"]["value"] = 3000
    _, _, c = calculation(b, locked)
    assert c["throat_area_m2"] == pytest.approx(2 * a["throat_area_m2"])
    assert c["mass_flow_kg_s"] == pytest.approx(2 * a["mass_flow_kg_s"])
    assert not c["engine_complete"]


def test_property_domain_gap_blocks_only_cold_hydraulics_not_ideal_performance():
    b = engine_brief()
    b["chamber_pressure"]["value"] = 600000
    _, design, r = calculation(b, {"mixture_ratio": {"value": 2.6, "unit": "1"}})
    assert design.workflow.current_result("performance") and r["injector"] is None
    assert (
        next(s for s in r["stages"] if s["name"] == "Cold injector hydraulics")["state"]
        == "BLOCKED"
    )


def test_conflicting_throat_lock_and_tampered_review_refused():
    with pytest.raises(InvalidInputError, match="conflict"):
        calculation(
            overrides={
                "mixture_ratio": {"value": 2.6, "unit": "1"},
                "throat_area": {"value": 0.1, "unit": "m2"},
            }
        )
    p = deepcopy(plan())
    p["effective"]["injector_cd"]["value"] = 0.9
    with pytest.raises(InvalidInputError, match="hash"):
        evaluate(p, None)


def test_vacuum_uses_reviewed_finite_expansion_not_infinite_matched_exit():
    b = engine_brief()
    b["environment"] = {"kind": "VACUUM"}
    b["burn_duration"] = None
    _, _, r = calculation(b, {"mixture_ratio": {"value": 2.8, "unit": "1"}})
    assert r["expansion_ratio"] == pytest.approx(20, rel=1e-8)
    assert r["propellant_mass_kg"] is None
