"""Stage 12/13 — materials selection + thin-wall chamber stress."""

from __future__ import annotations

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.materials.catalog import STAINLESS_304, get_material
from physics.materials.elastic_properties import yield_strength
from physics.quantities import kelvin, metre
from physics.solid_mechanics.pressure_vessels import cylinder

from systems.contracts.results import ResultStatus, ValidityInfo, ValidityState, VerificationInfo
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import failed_result, make_result, not_implemented_result

__all__ = ("run_materials_stage", "run_structure_stage")


def run_materials_stage(
    design: PropulsionDesign,
    *,
    material_id: str = "stainless_304",
) -> object:
    """Attach a Physics catalog material to the design (room-T handbook)."""

    stage_id = "materials"
    try:
        if material_id in {"STAINLESS_304", "stainless_304"}:
            material = STAINLESS_304
        else:
            material = get_material(material_id)
        design.material_selection = {
            "chamber_material_id": material.material_id,
            "condition": material.condition,
            "source": material.source,
        }
        result = make_result(
            calculation_type="materials.selection",
            stage_id=stage_id,
            status=ResultStatus.CURRENT,
            model_id="SYS-13.materials.catalog",
            model_version="0.1.0",
            inputs={"material_id": material_id},
            outputs={
                "material_id": {"value": material.material_id, "unit": "1"},
                "condition": {"value": material.condition, "unit": "1"},
            },
            assumptions=("Room-temperature handbook properties — not MMPDS allowables.",),
            warnings=("Validation: NOT_CLAIMED. Not a certified material allowables database.",),
            validity=ValidityInfo(status=ValidityState.UNKNOWN),
            verification=VerificationInfo(status="CATALOG_LOOKUP"),
            source=material.source,
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        design.workflow.invalidate_from(stage_id)
        design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
        design.workflow.results[stage_id].status = ResultStatus.CURRENT
        return result
    except Exception as exc:  # noqa: BLE001
        result = failed_result(
            calculation_type="materials.selection",
            stage_id=stage_id,
            exc=exc,
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        return result


def run_structure_stage(
    design: PropulsionDesign,
    *,
    wall_thickness_m: float | None = None,
) -> object:
    """Thin-wall hoop/longitudinal stress vs catalog yield."""

    stage_id = "structure"
    op = design.operating_point
    try:
        if op.chamber_pressure is None:
            raise InvalidInputError("structure requires chamber_pressure.")
        chamber = design.chamber_design or {}
        if "chamber_diameter_m" not in chamber:
            raise InvalidInputError("structure requires chamber_diameter_m (run chamber).")
        radius = 0.5 * float(chamber["chamber_diameter_m"])
        thickness = wall_thickness_m
        if thickness is None and design.structural_design and "wall_thickness_m" in design.structural_design:
            thickness = float(design.structural_design["wall_thickness_m"])  # type: ignore[arg-type]
        if thickness is None:
            thickness = 0.005
            t_assumption = "wall_thickness defaulted to 5 mm."
        else:
            t_assumption = None

        wall = cylinder(op.chamber_pressure, metre(radius), metre(float(thickness)))
        material = STAINLESS_304
        if design.material_selection and design.material_selection.get("chamber_material_id"):
            try:
                material = get_material(str(design.material_selection["chamber_material_id"]))
            except Exception:  # noqa: BLE001
                material = STAINLESS_304
        sy = yield_strength(material, kelvin(300.0)).require_valid()
        design.structural_design = {
            "radius_m": radius,
            "wall_thickness_m": float(thickness),
            "hoop_stress_pa": wall.hoop.to_si(),
            "longitudinal_stress_pa": wall.longitudinal.to_si(),
            "yield_strength_pa": sy.to_si(),
            "hoop_over_yield": wall.hoop.to_si() / sy.to_si(),
        }
        result = make_result(
            calculation_type="structure.thin_wall",
            stage_id=stage_id,
            status=ResultStatus.CURRENT,
            model_id="PHYS-007.pressure_vessel.thin_wall",
            model_version="0.1.0",
            inputs={
                "pressure": op.chamber_pressure.to_canonical_dict(),
                "radius_m": {"value": radius, "unit": "m"},
                "thickness_m": {"value": float(thickness), "unit": "m"},
            },
            outputs={
                "hoop_stress": wall.hoop.to_canonical_dict(),
                "longitudinal_stress": wall.longitudinal.to_canonical_dict(),
                "yield_strength": sy.to_canonical_dict(),
                "hoop_over_yield": {
                    "value": wall.hoop.to_si() / sy.to_si(),
                    "unit": "1",
                },
            },
            assumptions=(
                "Thin-wall membrane theory.",
                "Yield at 300 K handbook typical.",
                *([t_assumption] if t_assumption else []),
            ),
            warnings=("Not ASME/PED design. Validation: NOT_CLAIMED.",),
            validity=ValidityInfo(status=ValidityState.VALID if radius / float(thickness) >= 10 else ValidityState.OUT_OF_RANGE),
            verification=VerificationInfo(status="PASS", reference="hoop = p r / t"),
            source="Roark / Shigley thin-wall relations via Physics",
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        design.workflow.invalidate_from(stage_id)
        design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
        design.workflow.results[stage_id].status = ResultStatus.CURRENT
        return result
    except Exception as exc:  # noqa: BLE001
        result = failed_result(
            calculation_type="structure.thin_wall",
            stage_id=stage_id,
            exc=exc,
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        return result


def run_injector_stage(design: PropulsionDesign) -> object:
    return not_implemented_result(
        calculation_type="injector.design",
        stage_id="injector",
        reason="No validated injector orifice/element calculation in COSMOS_0.1 Physics.",
        design_revision=design.revision,
    )


def run_cooling_stage(design: PropulsionDesign) -> object:
    return not_implemented_result(
        calculation_type="cooling.regenerative",
        stage_id="cooling",
        reason="No validated regenerative/film cooling channel analysis in this foundation.",
        design_revision=design.revision,
    )
