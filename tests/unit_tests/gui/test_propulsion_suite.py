"""Unit tests for Rocket Engine propulsion suite catalog."""

from __future__ import annotations

from gui.workbenches.propulsion_suite import PROPULSION_SUITE_MODULES, suite_module_by_id
from gui.workbenches.registry import workbench_by_id


def test_suite_has_live_nozzle_and_heat_transfer() -> None:
    ids = [m.module_id for m in PROPULSION_SUITE_MODULES]
    assert "nozzle-flow" in ids
    assert "heat-transfer" in ids
    assert "propulsion" not in ids  # suite is not a top-level nav item
    nozzle = suite_module_by_id("nozzle-flow")
    heat = suite_module_by_id("heat-transfer")
    assert nozzle is not None and nozzle.status == "live"
    assert heat is not None and heat.status == "live"
    assert "isentropic_stagnation" in nozzle.physics_ops
    assert "bartz" in heat.physics_ops


def test_rocket_engine_workbench_points_at_suite() -> None:
    rocket = workbench_by_id("rocket-engine")
    assert rocket is not None
    assert rocket.route == "/app/workbench/rocket-engine"
    assert "Propulsion Design Suite" in rocket.modules
    assert len(rocket.modules) == 6
