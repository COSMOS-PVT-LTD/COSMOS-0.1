"""Persistence tests for propulsion design store."""

from __future__ import annotations

from pathlib import Path

from core.quantity import Quantity
from core.unit import SI

from systems.persistence.design_store import DesignStore
from systems.projects.models import PropulsionDesign


def test_save_and_reload_design(tmp_path: Path) -> None:
    store = DesignStore(tmp_path)
    design = PropulsionDesign(name="Persist Me", engineer="TK")
    design.requirements.target_thrust = Quantity(10000.0, SI.get("N"))
    store.save(design)
    loaded = store.load(design.design_id)
    assert loaded.name == "Persist Me"
    assert loaded.requirements.target_thrust is not None
    assert loaded.requirements.target_thrust.to_si() == 10000.0
    assert design.design_id in store.list_design_ids()
