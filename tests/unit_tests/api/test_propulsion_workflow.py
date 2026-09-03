"""API adapter tests for propulsion workflow boundary."""

from __future__ import annotations

from pathlib import Path

import pytest

from api.propulsion_workflow import (
    create_design,
    get_workflow_payload,
    run_isentropic,
    save_design,
    load_design,
    update_requirements,
)
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
