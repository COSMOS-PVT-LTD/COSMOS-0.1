"""Subsystem API/persistence/freshness regression tests."""

import copy
import math
from types import SimpleNamespace

import pytest

from api.propulsion_workflow import (
    export_design,
    load_design,
    run_subsystems,
    save_design,
)
from core.exceptions import InvalidInputError
from systems.contracts.results import ResultStatus
from systems.persistence.design_store import DesignStore
from systems.workflow.graph import (
    DependencyRequirement,
    StageDependency,
    StageImplementationStatus,
)
from systems.workflow.state import WorkflowState
from tests.fixtures.propulsion_subsystems import (
    cooling_inputs,
    film_inputs,
    injector_inputs,
    nozzle_inputs,
    seeded_design,
)


def test_subsystems_execute_persist_and_export_without_cycle_claim(tmp_path):
    design = seeded_design()
    store = DesignStore(tmp_path)
    result = run_subsystems(
        design,
        inputs={
            "injector": injector_inputs(),
            "nozzle": nozzle_inputs(),
            "cooling": cooling_inputs(),
        },
        store=store,
    )
    assert result["execution_ok"] is True
    assert result["workflow_complete"] is False
    assert result["validation_level"] == "NOT_CLAIMED"
    assert "cycle" in result["missing_stages"]
    assert all(row["status"] == "CURRENT" for row in result["stages"].values())
    assert len(result["stages"]["nozzle"]["outputs"]["stations"]) == 81
    assert abs(result["stages"]["cooling"]["outputs"]["energy_residual_w"]) < 1e-6
    restored = load_design(design.design_id, store)
    assert restored.subsystem_inputs == design.subsystem_inputs
    assert len(restored.nozzle_design["stations"]) == 81
    assert restored.workflow.current_result("cooling")
    exported = export_design(restored)
    assert "cooling" in exported["current_results"]
    assert exported["design"]["subsystem_inputs"]["injector"]["property_source"]


def test_film_changes_heat_load_and_preserves_slot_boundary():
    design = seeded_design()
    plain = run_subsystems(
        design,
        inputs={"nozzle": nozzle_inputs(), "cooling": cooling_inputs()},
        stages=("nozzle", "cooling"),
    )
    assert plain["execution_ok"]
    baseline = plain["stages"]["cooling"]["outputs"]["total_heat_w"]
    film = run_subsystems(
        design,
        inputs={"cooling": cooling_inputs() | film_inputs()},
        stages=("cooling",),
    )
    assert film["execution_ok"]
    outputs = film["stages"]["cooling"]["outputs"]
    assert outputs["total_heat_w"] < baseline
    assert outputs["film_mass_flow_estimate_kg_s"] > 0
    assert all(
        row["film_effectiveness"] == 0
        for row in outputs["segments"]
        if row["x_m"] < 0.04
    )
    assert any(
        row["film_effectiveness"] > 0
        for row in outputs["segments"]
        if row["x_m"] > 0.04
    )


def test_config_change_stales_only_data_consumers_and_excludes_export(tmp_path):
    design = seeded_design()
    run_subsystems(
        design,
        inputs={
            "injector": injector_inputs(),
            "nozzle": nozzle_inputs(),
            "cooling": cooling_inputs(),
        },
    )
    store = DesignStore(tmp_path)
    save_design(
        design, store, edits={"subsystem_inputs": {"nozzle": nozzle_inputs(161)}}
    )
    assert design.workflow.current_result("performance") is not None
    assert design.workflow.current_result("nozzle") is None
    assert design.workflow.results["cooling"].status is ResultStatus.STALE
    assert design.cooling_design["geometry_status"] == "STALE"
    assert "cooling" not in export_design(design)["current_results"]
    fail = run_subsystems(design, stages=("cooling",))
    assert not fail["execution_ok"]
    assert "nozzle" in fail["stages"]["cooling"]["errors"][0]["message"]
    fixed = run_subsystems(design, stages=("nozzle", "cooling"))
    assert fixed["execution_ok"]
    thermal_id = design.workflow.results["thermal"].result_id
    only_injector = run_subsystems(
        design,
        inputs={"injector": injector_inputs() | {"fuel_cd": 0.75}},
        stages=("injector",),
    )
    assert only_injector["execution_ok"]
    assert design.workflow.current_result("cooling") is not None
    assert design.workflow.results["thermal"].result_id == thermal_id


def test_failures_replace_success_and_never_reuse_old_cooling():
    design = seeded_design()
    run_subsystems(
        design,
        inputs={"nozzle": nozzle_inputs(), "cooling": cooling_inputs()},
        stages=("nozzle", "cooling"),
    )
    failure = run_subsystems(
        design,
        inputs={"cooling": cooling_inputs() | {"max_wall_temperature_k": 300}},
        stages=("cooling",),
    )
    assert not failure["execution_ok"]
    assert failure["stages"]["cooling"]["status"] == "OUT_OF_RANGE"
    assert design.workflow.current_result("cooling") is None
    assert design.cooling_design["geometry_status"] == "STALE"
    assert "cooling" not in export_design(design)["current_results"]


@pytest.mark.parametrize(
    "updates",
    [
        {"injector": {"fuel_cd": math.nan}},
        {"injector": {"fuel_hole_count": 1.5}},
        {"cooling": {"channel_count": True}},
        {"nozzle": {"invented": 1}},
        {"cycle": {}},
    ],
)
def test_config_validation_is_atomic(tmp_path, updates):
    design = seeded_design()
    before = copy.deepcopy(design.to_canonical_dict())
    with pytest.raises(InvalidInputError):
        save_design(design, DesignStore(tmp_path), edits={"subsystem_inputs": updates})
    assert design.to_canonical_dict() == before


def test_missing_inputs_fail_explicit_requests_and_clear_saved_values(tmp_path):
    design = seeded_design()
    direct = run_subsystems(design, stages=("injector", "nozzle", "cooling"))
    assert direct["execution_ok"] is False
    assert direct["stages"]["injector"]["status"] == "FAILED"
    assert direct["stages"]["nozzle"]["status"] == "FAILED"
    run_subsystems(design, inputs={"injector": injector_inputs()}, stages=("injector",))
    save_design(
        design,
        DesignStore(tmp_path),
        edits={"subsystem_inputs": {"injector": injector_inputs() | {"fuel_cd": None}}},
    )
    assert "fuel_cd" not in design.subsystem_inputs["injector"]
    assert run_subsystems(design, stages=("injector",))["execution_ok"] is False


def test_bell_cooling_grid_convergence():
    heats, losses = [], []
    for count in (41, 81, 161, 321):
        design = seeded_design()
        result = run_subsystems(
            design,
            inputs={"nozzle": nozzle_inputs(count), "cooling": cooling_inputs()},
            stages=("nozzle", "cooling"),
        )
        assert result["execution_ok"]
        outputs = result["stages"]["cooling"]["outputs"]
        heats.append(outputs["total_heat_w"])
        losses.append(outputs["total_pressure_loss_pa"])
    assert abs(heats[-1] - heats[-2]) < abs(heats[1] - heats[0])
    assert abs(losses[-1] - losses[-2]) < abs(losses[1] - losses[0])
    assert abs(heats[-1] - heats[-2]) / heats[-1] < 0.002


@pytest.mark.parametrize(
    "override",
    [
        {"film_valid_length_m": 0.001},
        {"film_slot_x_m": 2},
        {"film_source": ""},
        {"film_delta_growth_rate": -1},
    ],
)
def test_film_refuses_missing_provenance_or_uncovered_profile(override):
    design = seeded_design()
    result = run_subsystems(
        design,
        inputs={
            "nozzle": nozzle_inputs(),
            "cooling": cooling_inputs() | film_inputs() | override,
        },
        stages=("nozzle", "cooling"),
    )
    assert not result["execution_ok"]
    assert design.workflow.current_result("cooling") is None


def test_injector_rejects_non_liquid_registry_phase(monkeypatch):
    from physics.thermochemistry.propellants import Phase

    monkeypatch.setattr(
        "systems.stages.subsystems.get_propellant_by_alias",
        lambda _: SimpleNamespace(phase=Phase.GAS),
    )
    design = seeded_design()
    result = run_subsystems(
        design, inputs={"injector": injector_inputs()}, stages=("injector",)
    )
    assert result["stages"]["injector"]["status"] == "OUT_OF_RANGE"


def test_saved_injector_runs_after_cold_registry_restart(tmp_path):
    from physics.thermochemistry.propellants import clear_registry

    design = seeded_design()
    store = DesignStore(tmp_path)
    run_subsystems(
        design,
        inputs={"injector": injector_inputs()},
        stages=("injector",),
        store=store,
    )
    clear_registry()  # Simulate restarting the desktop process, retaining its saved design.
    restored = load_design(design.design_id, store)
    result = run_subsystems(restored, stages=("injector",))
    assert result["execution_ok"]
    assert result["stages"]["injector"]["inputs"][
        "propellant_registry_source"
    ].endswith("propellants_master_candidate_v1.json")


def test_saved_legacy_workflow_edges_migrate_without_claiming_new_results():
    workflow = WorkflowState()
    workflow.graph.get("nozzle").dependencies = (
        StageDependency("chamber", DependencyRequirement.INFORMATIONAL),
        StageDependency("cooling", DependencyRequirement.DEFERRED),
        StageDependency("performance"),
    )
    workflow.graph.get("cooling").dependencies = (StageDependency("thermal"),)
    workflow.graph.get(
        "cooling"
    ).implementation_status = StageImplementationStatus.NOT_IMPLEMENTED
    workflow.graph.get("chamber").dependencies = (
        StageDependency("performance"),
        StageDependency("injector", DependencyRequirement.DEFERRED),
    )
    workflow.mark_not_implemented("cooling", "Legacy placeholder")
    migrated = WorkflowState.from_canonical_dict(workflow.to_canonical_dict())
    assert {edge.stage_id for edge in migrated.graph.get("cooling").dependencies} == {
        "thermal",
        "nozzle",
    }
    assert "cooling" not in {
        edge.stage_id for edge in migrated.graph.get("nozzle").dependencies
    }
    assert (
        migrated.graph.get("chamber").dependencies[-1].requirement
        is DependencyRequirement.INFORMATIONAL
    )
    assert migrated.current_result("cooling") is None
    assert migrated.results["cooling"].status is ResultStatus.NOT_IMPLEMENTED


def test_workflow_reload_preserves_custom_dependencies():
    workflow = WorkflowState()
    custom = (StageDependency("performance"), StageDependency("thermal"))
    workflow.graph.get("nozzle").dependencies = custom
    restored = WorkflowState.from_canonical_dict(workflow.to_canonical_dict())
    assert restored.graph.get("nozzle").dependencies == custom


def test_legacy_migration_preserves_custom_requirement_roles():
    workflow = WorkflowState()
    custom = (
        StageDependency("chamber", DependencyRequirement.OPTIONAL),
        StageDependency("performance"),
        StageDependency("cooling", DependencyRequirement.DEFERRED),
    )
    workflow.graph.get("nozzle").dependencies = custom
    workflow.graph.get("cooling").dependencies = (StageDependency("thermal"),)
    workflow.graph.get(
        "cooling"
    ).implementation_status = StageImplementationStatus.NOT_IMPLEMENTED
    restored = WorkflowState.from_canonical_dict(workflow.to_canonical_dict())
    assert restored.graph.get("nozzle").dependencies == custom
