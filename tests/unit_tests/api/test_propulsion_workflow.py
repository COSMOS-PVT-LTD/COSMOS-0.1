"""API adapter tests for propulsion workflow boundary."""

from __future__ import annotations

from pathlib import Path

import pytest

from api.propulsion_workflow import (
    create_design,
    get_workflow_payload,
    load_design,
    run_isentropic,
    save_design,
    update_requirements,
)
from core.exceptions import InvalidInputError
from systems.contracts.results import ResultStatus
from systems.persistence.design_store import DesignStore


def test_api_create_update_calculate_reload(tmp_path: Path) -> None:
    store = DesignStore(tmp_path)
    design = create_design(name="API Design", engineer="TK", store=store)
    update_requirements(
        design,
        {"target_chamber_pressure": 7.0e6, "mixture_ratio": 2.3},
        store=store,
    )
    result = run_isentropic(design, mach=2.0, gamma=1.4, store=store)
    assert result.status is ResultStatus.CURRENT
    loaded = load_design(design.design_id, store)
    assert loaded.requirements.mixture_ratio == pytest.approx(2.3)
    assert loaded.workflow.results["nozzle"].status is ResultStatus.CURRENT
    workflow = get_workflow_payload(loaded)
    nozzle = next(node for node in workflow["nodes"] if node["stage_id"] == "nozzle")
    assert nozzle["result_is_current"] is True


def test_save_design_helper(tmp_path: Path) -> None:
    store = DesignStore(tmp_path)
    design = create_design(name="Save Helper")
    path = save_design(design, store)
    assert path.is_file()


def test_save_editor_edits_persists_inputs_without_calculating(tmp_path: Path) -> None:
    store = DesignStore(tmp_path)
    design = create_design(name="Save edits", store=store)
    save_design(design, store, edits={
        "base_revision": 0, "name": "Renamed",
        "requirements": {"target_chamber_pressure": {"magnitude": 50, "unit_symbol": "bar"},
                         "target_thrust": {"magnitude": 10, "unit_symbol": "kN"},
                         "ambient_pressure": {"magnitude": 0, "unit_symbol": "Pa"}},
        "propellants": {"oxidizer_id": "LOX", "fuel_id": "RP1", "mixture_ratio": 2.3},
        "editor_drafts": {"wf-tc": "3000", "wf-pout": "0", "wf-curvature": ""},
    })
    loaded = load_design(design.design_id, store)
    assert loaded.name == "Renamed"
    assert loaded.requirements.target_chamber_pressure.to_si() == 5_000_000
    assert loaded.requirements.target_thrust.to_si() == 10_000
    assert loaded.requirements.ambient_pressure.magnitude == 0
    assert loaded.editor_drafts == {"wf-tc": "3000", "wf-pout": "0", "wf-curvature": ""}
    assert loaded.operating_point.chamber_temperature is None
    assert loaded.workflow.results == {}
    assert loaded.nozzle_design is None


def test_editor_save_invalidates_results_only_for_applied_inputs(tmp_path: Path) -> None:
    store = DesignStore(tmp_path)
    design = create_design(name="Freshness", store=store)
    run_isentropic(design, mach=2.0, gamma=1.4, store=store)
    save_design(design, store, edits={"editor_drafts": {"wf-gamma": "1.2"}})
    assert design.workflow.results["nozzle"].status is ResultStatus.CURRENT
    save_design(design, store, edits={"requirements": {"target_chamber_pressure": 5_000_000}})
    assert design.workflow.results["nozzle"].status is ResultStatus.STALE
    assert load_design(design.design_id, store).workflow.results["nozzle"].status is ResultStatus.STALE


@pytest.mark.parametrize("edits", [
    {"base_revision": 999, "name": "Wrong revision"},
    {"editor_drafts": {"wf-tc": 3000}},
    {"name": "   "},
    {"requirements": {"target_thrust": 1000}, "propellants": {"store": "unsafe"}},
])
def test_rejected_editor_save_is_atomic(tmp_path: Path, edits: dict) -> None:
    store = DesignStore(tmp_path)
    design = create_design(name="Unchanged", store=store)
    before = design.to_canonical_json()
    with pytest.raises(InvalidInputError):
        save_design(design, store, edits=edits)
    assert design.to_canonical_json() == before
    assert load_design(design.design_id, store).to_canonical_json() == before
