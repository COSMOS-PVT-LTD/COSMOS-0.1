"""Unit tests for workbench registry."""

from __future__ import annotations

from gui.workbenches.registry import WORKBENCH_PAGES, workbench_by_id


def test_registry_contains_core_workbenches() -> None:
    rocket_engine = workbench_by_id("rocket-engine")
    knowledge = workbench_by_id("knowledge")
    assert rocket_engine is not None
    assert knowledge is not None
    assert rocket_engine.page == 1
    assert len(rocket_engine.modules) == 6
    assert len(WORKBENCH_PAGES) == 3
    page_one_ids = [item.workbench_id for item in WORKBENCH_PAGES[0]]
    page_two_ids = [item.workbench_id for item in WORKBENCH_PAGES[1]]
    assert page_one_ids == ["rocket-engine", "turbopumps", "pid", "structures"]
    assert page_two_ids == ["rocket-staging", "manufacturing", "simulation", "visualization"]
