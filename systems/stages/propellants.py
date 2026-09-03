"""Stage 02 — propellant configuration against Physics registry."""

from __future__ import annotations

from pathlib import Path

from physics.thermochemistry.propellants import (
    PropellantNotFoundError,
    clear_registry,
    get_propellant_by_alias,
    load_json_database,
    registry_size,
)

from systems.contracts.results import ResultStatus, ValidityInfo, ValidityState, VerificationInfo
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import failed_result, make_result

__all__ = ("run_propellants_stage",)

_CANDIDATE_DB = (
    Path(__file__).resolve().parents[2]
    / "physics"
    / "thermochemistry"
    / "database"
    / "propellants_master_candidate_v1.json"
)


def _ensure_registry_loaded() -> str:
    """Load the verified candidate propellant DB if registry is empty."""

    if registry_size() > 0:
        return "already_loaded"
    if not _CANDIDATE_DB.is_file():
        raise PropellantNotFoundError(
            f"Propellant database missing: {_CANDIDATE_DB}. "
            "Cannot resolve oxidizer/fuel without Physics registry data."
        )
    clear_registry()
    load_json_database(_CANDIDATE_DB)
    return str(_CANDIDATE_DB)


def run_propellants_stage(design: PropulsionDesign) -> object:
    """
    Resolve oxidizer/fuel IDs via Physics propellant registry.

    Does not compute combustion properties.
    """

    stage_id = "propellants"
    cfg = design.propellant_configuration

    # Allow requirements.propellant_selection like "LOX/RP-1" to seed IDs.
    if (cfg.oxidizer_id is None or cfg.fuel_id is None) and design.requirements.propellant_selection:
        parts = str(design.requirements.propellant_selection).replace(" ", "").split("/")
        if len(parts) == 2:
            if cfg.oxidizer_id is None:
                cfg.oxidizer_id = parts[0]
            if cfg.fuel_id is None:
                cfg.fuel_id = parts[1]

    if design.requirements.mixture_ratio is not None and cfg.mixture_ratio is None:
        cfg.mixture_ratio = float(design.requirements.mixture_ratio)

    try:
        db_note = _ensure_registry_loaded()
        if not cfg.oxidizer_id or not cfg.fuel_id:
            raise PropellantNotFoundError(
                "oxidizer_id and fuel_id are required (or propellant_selection 'OX/FUEL')."
            )
        oxidizer = get_propellant_by_alias(cfg.oxidizer_id)
        fuel = get_propellant_by_alias(cfg.fuel_id)
        # Normalize stored IDs to canonical short names.
        cfg.oxidizer_id = oxidizer.short_name
        cfg.fuel_id = fuel.short_name
        result = make_result(
            calculation_type="workflow.propellants",
            stage_id=stage_id,
            status=ResultStatus.CURRENT,
            model_id="SYS-02.propellants.registry",
            model_version="0.1.0",
            inputs={**cfg.to_canonical_dict(), "database": db_note},
            outputs={
                "oxidizer_name": {"value": oxidizer.name, "unit": "1"},
                "fuel_name": {"value": fuel.name, "unit": "1"},
                "oxidizer_cea_species": {"value": oxidizer.cea_species_name, "unit": "1"},
                "fuel_cea_species": {"value": fuel.cea_species_name, "unit": "1"},
                "oxidizer_mw_kg_per_kmol": {
                    "value": float(oxidizer.molecular_weight),
                    "unit": "kg/kmol",
                },
                "fuel_mw_kg_per_kmol": {
                    "value": float(fuel.molecular_weight),
                    "unit": "kg/kmol",
                },
                "mixture_ratio": {
                    "value": cfg.mixture_ratio,
                    "unit": "1",
                },
            },
            assumptions=(
                "Registry lookup only — no combustion equilibrium evaluated.",
                "Database: propellants_master_candidate_v1.json (Physics).",
            ),
            warnings=(),
            validity=ValidityInfo(status=ValidityState.VALID),
            verification=VerificationInfo(
                status="PASS",
                reference="Physics propellant registry identity",
            ),
            source=f"oxidizer={oxidizer.source}; fuel={fuel.source}",
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        design.workflow.invalidate_from(stage_id)
        design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
        design.workflow.results[stage_id].status = ResultStatus.CURRENT
        return result
    except Exception as exc:  # noqa: BLE001
        result = failed_result(
            calculation_type="workflow.propellants",
            stage_id=stage_id,
            exc=exc,
            design_revision=design.revision,
            inputs=cfg.to_canonical_dict(),
        )
        design.store_stage_result(stage_id, result)
        return result
