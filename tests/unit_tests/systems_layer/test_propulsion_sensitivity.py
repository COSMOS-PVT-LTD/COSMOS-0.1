"""Existing-model OAT sensitivity; fixtures are software evidence only."""

from __future__ import annotations

import json
from hashlib import sha256

import pytest

from api.propulsion_workflow import (
    create_design,
    run_phase3,
    update_propellants,
    update_requirements,
)
from api.sensitivity_projects import evaluate
from systems.projects.authority import InvalidRecord
from systems.projects.sensitivity import study, validate


@pytest.fixture(autouse=True)
def isolated_propellant_catalog(monkeypatch):
    # Core isolation tests intentionally unload Physics from sys.modules. The
    # previously imported API catalog functions can retain their earlier module
    # globals while dynamic imports see a new Physics module. Isolate and seed
    # both real registries; do not change production import/catalog behavior.
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


def baseline():
    design = create_design(name="Sensitivity software fixture")
    update_requirements(
        design,
        {
            "target_chamber_pressure": 5e6,
            "target_thrust": 10000,
            "ambient_pressure": 0.0,
            "expansion_ratio": 10.0,
            "mixture_ratio": 2.3,
        },
    )
    update_propellants(design, oxidizer_id="LOX", fuel_id="RP1", mixture_ratio=2.3)
    outcome = run_phase3(
        design,
        chamber_temperature_k=3000.0,
        gamma=1.2,
        molecular_weight_kg_per_mol=0.022,
        throat_area_m2=0.001,
        expansion_ratio=10.0,
    )
    assert outcome["ok"]
    return design


def specification(**edits):
    return {
        "parameter": "throat_area_m2",
        "unit": "m2",
        "values": [0.0008, 0.001, 0.0012],
        "output": "thrust",
        "step": 0.00001,
        **edits,
    }


@pytest.mark.parametrize(
    "parameter,unit,values,h",
    [
        ("chamber_pressure_pa", "Pa", [4e6, 5e6, 6e6], 1000.0),
        ("ambient_pressure_pa", "Pa", [0.0, 500.0, 1000.0], 100.0),
        ("throat_area_m2", "m2", [0.0008, 0.001, 0.0012], 1e-5),
        ("expansion_ratio", "1", [8.0, 10.0, 12.0], 0.1),
    ],
)
@pytest.mark.parametrize(
    "output,expected_unit",
    [
        ("thrust", "N"),
        ("mass_flow", "kg/s"),
        ("specific_impulse", "s"),
        ("exit_velocity", "m/s"),
    ],
)
def test_all_declared_parameter_output_pairs_retain_existing_model_values(
    parameter, unit, values, h, output, expected_unit
):
    design = baseline()
    result = study(
        design,
        specification(
            parameter=parameter, unit=unit, values=values, step=h, output=output
        ),
        evaluate,
    )
    assert result["status"] == "COMPLETED" and result["output_unit"] == expected_unit
    for row in result["samples"]:
        original = evaluate(baseline(), parameter, row["value"])["performance"][
            "outputs"
        ][output]
        expected = (
            original["magnitude"] if "magnitude" in original else original["value"]
        )
        assert row["output"] == expected


@pytest.mark.parametrize(
    "parameter,unit,values,h",
    [
        ("throat_area_m2", "m2", [0.0008, 0.001, 0.0012], 1e-5),
        ("chamber_pressure_pa", "Pa", [4e6, 5e6, 6e6], 1000.0),
    ],
)
def test_existing_model_linear_scaling_units_original_bytes_and_step_refinement(
    parameter, unit, values, h
):
    design = baseline()
    original = design.to_canonical_json()
    result = study(
        design,
        specification(parameter=parameter, unit=unit, values=values, step=h),
        evaluate,
    )
    expected = result["baseline_output"] / result["baseline_parameter"]
    assert result["status"] == "COMPLETED"
    assert [row["output"] / row["value"] for row in result["samples"]] == pytest.approx(
        [expected] * 3, rel=1e-10
    )
    assert [row["value"] for row in result["derivatives"]] == pytest.approx(
        [expected] * 2, rel=1e-9
    )
    assert result["derivative_unit"] == "N/(" + unit + ")"
    assert (
        result["uncertainty"] == "NOT_QUANTIFIED"
        and result["physical_validation"] == "NOT_PERFORMED"
    )
    assert design.to_canonical_json() == original
    for row in result["evaluations"]:
        assert (
            json.loads(row["performance_canonical_json"])["result_id"]
            == row["performance"]["result_id"]
        )
        assert len(sha256(row["input_canonical_json"].encode()).hexdigest()) == 64


def test_invalid_samples_and_center_stencils_remain_explicit_no_one_sided_fallback():
    result = study(
        baseline(),
        specification(
            parameter="ambient_pressure_pa",
            unit="Pa",
            values=[-100.0, 0.0, 100.0],
            step=10.0,
        ),
        evaluate,
    )
    assert result["status"] == "COMPLETED_WITH_INVALID_DOMAINS"
    assert [row["status"] for row in result["samples"]] == [
        "INVALID_DOMAIN",
        "EVALUATED",
        "EVALUATED",
    ]
    assert all(
        row["status"] == "UNAVAILABLE" and row["value"] is None
        for row in result["derivatives"]
    )
    assert result["step_refinement_absolute_difference"] is None
    assert any(row["value"] == -5.0 for row in result["evaluations"])


@pytest.mark.parametrize(
    "edits",
    [
        {"unit": "bar"},
        {"values": [1.0, 1.0, 2.0]},
        {"values": [1.0, float("nan"), 2.0]},
        {"values": [1.0, True, 2.0]},
        {"values": [1.0, 2.0]},
        {"values": list(range(22))},
        {"step": 0.0},
        {"step": True},
        {"step": float("inf")},
        {"output": "cycle_power"},
        {"parameter": []},
        {"results": []},
    ],
)
def test_invalid_requests_are_not_inferred_or_defaulted(edits):
    with pytest.raises(InvalidRecord):
        validate(specification(**edits))


def test_spacing_and_cea_refusal_are_not_silent_model_changes():
    design = baseline()
    with pytest.raises(InvalidRecord, match="spacing"):
        study(design, specification(step=1e-30), evaluate)
    design.thermochemistry_configuration = {"mode": "nasa_cea"}
    with pytest.raises(InvalidRecord, match="CEA"):
        study(design, specification(), evaluate)


def test_centered_difference_step_refinement_against_independent_cubic_function():
    # Numerical-method fixture, not an engine equation or hardware reference.
    def cubic(_design, _parameter, x):
        return {
            "performance": {
                "status": "CURRENT",
                "validity": {"status": "VALID"},
                "outputs": {"thrust": {"value": x**3}},
                "errors": [],
            }
        }

    result = study(baseline(), specification(step=0.0001), cubic)
    x = result["baseline_parameter"]
    for derivative in result["derivatives"]:
        assert derivative["value"] == pytest.approx(
            3 * x * x + derivative["step"] ** 2, rel=1e-10
        )
    assert result["step_refinement_absolute_difference"] == pytest.approx(
        0.75 * 0.0001**2, rel=1e-8
    )


@pytest.mark.parametrize("fault", ["failure", "method-drift", "late-edit"])
def test_durable_capture_failure_method_drift_and_late_source_edit(tmp_path, fault):
    from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
    from systems.persistence.project_repository import RecordPayload
    from systems.projects.authority import Head, IntegrityFailure, Principal
    from systems.projects.sensitivity import DOMAIN, INPUTS, ManagedSensitivity

    repo = SQLiteProjectRepository(tmp_path / "state")
    actor = Principal("USR-sensitivity-test", "ENGINEER")
    project = repo.create_project(
        actor, title="Storage software fixture", operation_id="project"
    )
    design = baseline()
    source = repo.save_snapshot(
        actor,
        project.project_id,
        domain="propulsion",
        object_id=design.design_id,
        input_revision=design.revision,
        payload=RecordPayload.from_design(design),
        expected=Head.absent(),
        operation_id="baseline",
    )
    hashes = {"fixture-method": "a" * 64}
    changed = False

    def computation(candidate, parameter, x):
        nonlocal changed
        if not changed:
            changed = True
            if fault == "failure":
                raise RuntimeError("Synthetic execution failure; no success record")
            if fault == "method-drift":
                hashes["fixture-method"] = "b" * 64
            if fault == "late-edit":
                altered = baseline()
                altered.design_id = design.design_id
                update_requirements(altered, {"target_chamber_pressure": 6e6})
                repo.save_snapshot(
                    actor,
                    project.project_id,
                    domain="propulsion",
                    object_id=design.design_id,
                    input_revision=altered.revision,
                    payload=RecordPayload.from_design(altered),
                    expected=source.head,
                    operation_id="late-edit",
                )
        return evaluate(candidate, parameter, x)

    service = ManagedSensitivity(repo, computation, lambda: dict(hashes))

    def create():
        return service.create(
            actor,
            project.project_id,
            source.commit_id,
            source.head,
            specification(),
            "analysis",
            "c" * 64,
        )

    if fault in {"failure", "method-drift"}:
        with pytest.raises(RuntimeError if fault == "failure" else IntegrityFailure):
            create()
        assert len(repo.list_objects(actor, project.project_id, domain=INPUTS)) == 1
        assert not repo.list_objects(actor, project.project_id, domain=DOMAIN)
        if fault == "failure":
            recovered = create()
            assert service.read(actor, recovered)["upstream_current"]
            assert create().commit_id == recovered.commit_id
    else:
        saved = create()
        assert not service.read(actor, saved)["upstream_current"]
        assert (
            service.read(actor, saved)["record"]["baseline_commit_id"]
            == source.commit_id
        )
