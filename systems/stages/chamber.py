"""Stage 08 — chamber geometry from throat area and L* (sizing only)."""

from __future__ import annotations

import math

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI

from systems.contracts.results import ResultStatus, ValidityInfo, ValidityState, VerificationInfo
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import failed_result, make_result

__all__ = ("run_chamber_stage",)


def run_chamber_stage(
    design: PropulsionDesign,
    *,
    characteristic_length_m: float | None = None,
    contraction_ratio: float | None = None,
) -> object:
    """
    Preliminary chamber sizing from At and L*.

    Vc = L* * At; approximate cylindrical chamber with contraction ratio.
    Not a validated combustor design method.
    """

    stage_id = "chamber"
    try:
        nozzle = design.nozzle_design or {}
        if "throat_area_m2" not in nozzle:
            raise InvalidInputError("chamber sizing requires nozzle throat_area_m2 (run performance).")
        at = float(nozzle["throat_area_m2"])
        lstar = characteristic_length_m
        if lstar is None and design.chamber_design and "characteristic_length_m" in design.chamber_design:
            lstar = float(design.chamber_design["characteristic_length_m"])  # type: ignore[arg-type]
        if lstar is None:
            lstar = 1.0
            lstar_assumption = "L* defaulted to 1.0 m (analysis assumption)."
        else:
            lstar_assumption = None
        cr = contraction_ratio if contraction_ratio is not None else 2.0
        cr_assumption = None if contraction_ratio is not None else "contraction_ratio defaulted to 2.0."

        volume = float(lstar) * at
        throat_diameter = 2.0 * math.sqrt(at / math.pi)
        chamber_area = float(cr) * at
        chamber_diameter = 2.0 * math.sqrt(chamber_area / math.pi)
        # Approximate cylindrical length from volume / Ac (ignores convergent).
        chamber_length = volume / chamber_area

        design.chamber_design = {
            "throat_area_m2": at,
            "throat_diameter_m": throat_diameter,
            "characteristic_length_m": float(lstar),
            "chamber_volume_m3": volume,
            "contraction_ratio": float(cr),
            "chamber_diameter_m": chamber_diameter,
            "chamber_length_m": chamber_length,
        }

        assumptions = [
            "Preliminary geometric sizing only (Vc = L* At).",
            "Cylindrical approximation; convergent/injector volume neglected.",
            *([lstar_assumption] if lstar_assumption else []),
            *([cr_assumption] if cr_assumption else []),
        ]
        result = make_result(
            calculation_type="chamber.preliminary_sizing",
            stage_id=stage_id,
            status=ResultStatus.CURRENT,
            model_id="SYS-08.chamber.lstar_geometry",
            model_version="0.1.0",
            inputs={
                "throat_area_m2": {"value": at, "unit": "m2"},
                "characteristic_length_m": {"value": float(lstar), "unit": "m"},
                "contraction_ratio": {"value": float(cr), "unit": "1"},
            },
            outputs={
                "chamber_volume": {"value": volume, "unit": "m3"},
                "throat_diameter": {"value": throat_diameter, "unit": "m"},
                "chamber_diameter": {"value": chamber_diameter, "unit": "m"},
                "chamber_length": {"value": chamber_length, "unit": "m"},
            },
            assumptions=tuple(assumptions),
            warnings=("Validation: NOT_CLAIMED. Not a combustor CFD/design code.",),
            validity=ValidityInfo(status=ValidityState.UNKNOWN),
            verification=VerificationInfo(status="SOFTWARE_IDENTITY"),
            source="Systems geometric relations (L* definition)",
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        design.workflow.invalidate_from(stage_id)
        design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
        design.workflow.results[stage_id].status = ResultStatus.CURRENT
        return result
    except Exception as exc:  # noqa: BLE001
        result = failed_result(
            calculation_type="chamber.preliminary_sizing",
            stage_id=stage_id,
            exc=exc,
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        return result
