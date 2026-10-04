"""Catalog and design-lifecycle API tests."""

from __future__ import annotations

from pathlib import Path

from api.catalogs import (
    list_material_catalog,
    list_propellant_catalog,
    list_workflow_catalog,
)
from api.propulsion_workflow import (
    clone_design,
    create_design,
    list_designs,
    update_propellants,
    update_requirements,
)
from systems.persistence.design_store import DesignStore


def test_propellant_catalog_uses_registry_ids() -> None:
    catalog = list_propellant_catalog()
    assert catalog["ok"] is True
    assert "LOX" in catalog["oxidizer_ids"]
    assert "RP1" in catalog["fuel_ids"]
    assert all("/" not in item["id"] for item in catalog["propellants"])


def test_material_catalog_is_not_certified() -> None:
    catalog = list_material_catalog()
    assert catalog["ok"] is True
    ids = {row["material_id"] for row in catalog["materials"]}
    assert "stainless_304" in ids
    assert all(row["certified_allowables"] is False for row in catalog["materials"])
    assert all(row["validation_state"] == "NOT_CLAIMED" for row in catalog["materials"])


def test_workflow_catalog_exposes_bypass_policy() -> None:
    catalog = list_workflow_catalog()
    chamber = next(node for node in catalog["nodes"] if node["stage_id"] == "chamber")
    assert any(item["upstream"] == "injector" for item in chamber["dependency_policy"])


def test_workflow_catalog_uses_stage_00_to_16_order() -> None:
    from systems.workflow.graph import PROPULSION_STAGE_SEQUENCE

    catalog = list_workflow_catalog()
    ids = [node["stage_id"] for node in catalog["nodes"]]
    assert ids == list(PROPULSION_STAGE_SEQUENCE)
    assert catalog["nodes"][0]["stage_index"] == "00"
    assert catalog["nodes"][-1]["stage_index"] == "16"
    assert catalog["nodes"][0]["stage_id"] == "design_project"
    assert catalog["nodes"][-1]["stage_id"] == "design_review"
    injector = next(node for node in catalog["nodes"] if node["stage_id"] == "injector")
    assert injector["calculate_supported"] is False
    assert injector["engineering_note"]


def test_list_clone_and_bar_units(tmp_path: Path) -> None:
    store = DesignStore(tmp_path)
    design = create_design(name="Unit Engine", store=store)
    update_requirements(
        design,
        {
            "target_chamber_pressure": {"magnitude": 70, "unit_symbol": "bar"},
            "target_thrust": {"magnitude": 10, "unit_symbol": "kN"},
        },
        store=store,
    )
    assert design.requirements.target_chamber_pressure is not None
    assert design.requirements.target_chamber_pressure.to_si() == 7.0e6
    assert design.requirements.target_thrust is not None
    assert design.requirements.target_thrust.to_si() == 10000.0
    update_propellants(design, oxidizer_id="LOX", fuel_id="RP1", mixture_ratio=2.6, store=store)
    rows = list_designs(store)
    assert any(row["design_id"] == design.design_id and row["name"] == "Unit Engine" for row in rows)
    cloned = clone_design(design, name="Unit Engine copy", store=store)
    assert cloned.design_id != design.design_id
    assert cloned.name == "Unit Engine copy"
    assert cloned.revision == 0
    assert store.exists(cloned.design_id)
