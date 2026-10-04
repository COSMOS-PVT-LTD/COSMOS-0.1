"""
Read-only engineering catalogs for the application API.

GUI → API only. Physics registries remain the source of identity.
"""

from __future__ import annotations

from pathlib import Path

from physics.materials.catalog import MATERIALS
from physics.thermochemistry.propellants import (
    PropellantType,
    clear_registry,
    list_propellants,
    load_json_database,
    registry_size,
)
from systems.workflow.graph import (
    BYPASSABLE_WHEN_UNIMPLEMENTED,
    STAGE_ENGINEERING_NOTES,
    StageImplementationStatus,
    build_default_propulsion_graph,
    ordered_stage_ids,
    stage_index,
)

__all__ = (
    "PROPELLANT_CANDIDATE_DB",
    "ensure_propellant_registry",
    "list_material_catalog",
    "list_propellant_catalog",
    "list_workflow_catalog",
)

PROPELLANT_CANDIDATE_DB: Path = (
    Path(__file__).resolve().parents[1]
    / "physics"
    / "thermochemistry"
    / "database"
    / "propellants_master_candidate_v1.json"
)


def ensure_propellant_registry() -> str:
    """Load the Physics candidate propellant database if the registry is empty."""

    if registry_size() > 0:
        return "already_loaded"
    if not PROPELLANT_CANDIDATE_DB.is_file():
        raise FileNotFoundError(f"Propellant database missing: {PROPELLANT_CANDIDATE_DB}")
    clear_registry()
    load_json_database(PROPELLANT_CANDIDATE_DB)
    return str(PROPELLANT_CANDIDATE_DB)


def list_propellant_catalog() -> dict[str, object]:
    """Canonical propellant IDs from Physics — not GUI strings such as 'LOX/RP-1'."""

    database = ensure_propellant_registry()
    rows = []
    for item in list_propellants():
        rows.append(
            {
                "id": item.short_name,
                "name": item.name,
                "short_name": item.short_name,
                "formula": item.formula,
                "propellant_type": item.propellant_type.value,
                "cea_species_name": item.cea_species_name,
                "aliases": list(item.aliases),
                "source": item.source,
                "availability": "REGISTRY",
            }
        )
    return {
        "ok": True,
        "database": database,
        "propellants": rows,
        "oxidizer_ids": [
            row["id"] for row in rows if row["propellant_type"] == PropellantType.OXIDIZER.value
        ],
        "fuel_ids": [
            row["id"] for row in rows if row["propellant_type"] == PropellantType.FUEL.value
        ],
        "authority": "physics.thermochemistry.propellants",
        "note": (
            "IDs are Physics registry short_name values. Concatenated pairs such as "
            "'LOX/RP-1' are display labels only."
        ),
    }


def list_material_catalog() -> dict[str, object]:
    rows = []
    for record in MATERIALS.values():
        rows.append(
            {
                "material_id": record.material_id,
                "condition": record.condition,
                "source": record.source,
                "property_model": "temperature-windowed handbook record",
                "reference_temperature_k": record.density.reference_temperature_k,
                "limitations": record.density.notes,
                "validation_state": "NOT_CLAIMED",
                "certified_allowables": False,
            }
        )
    return {
        "ok": True,
        "materials": rows,
        "authority": "physics.materials.catalog",
        "note": (
            "Room-temperature handbook values are not MMPDS/ASME certified design allowables."
        ),
    }


def list_workflow_catalog() -> dict[str, object]:
    graph = build_default_propulsion_graph()
    nodes = []
    for stage_id in ordered_stage_ids(graph.nodes):
        node = graph.nodes[stage_id]
        bypass = [
            {
                "upstream": upstream,
                "reason": reason,
            }
            for (downstream, upstream), reason in BYPASSABLE_WHEN_UNIMPLEMENTED.items()
            if downstream == stage_id
        ]
        impl = node.implementation_status
        nodes.append(
            {
                "stage_index": stage_index(stage_id),
                "stage_id": node.stage_id,
                "name": node.name,
                "dependencies": [edge.stage_id for edge in node.dependencies],
                "dependency_edges": [edge.to_canonical_dict() for edge in node.dependencies],
                "implementation_status": impl.value,
                "status": node.status.value,
                "dependency_policy": bypass,
                "engineering_note": STAGE_ENGINEERING_NOTES.get(stage_id, ""),
                "calculate_supported": impl
                is not StageImplementationStatus.NOT_IMPLEMENTED,
            }
        )
    return {
        "ok": True,
        "workflow_id": "propulsion.default",
        "nodes": nodes,
        "authority": "systems.workflow.graph",
        "stage_count": len(nodes),
    }
