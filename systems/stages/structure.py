"""Stage 12/13 — catalog materials and bounded smooth-cylinder pressure stress."""

from __future__ import annotations

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.validation import validate_positive
from physics.exceptions import InsufficientDataError, OutOfRangeError
from physics.materials.catalog import get_material
from physics.materials.elastic_properties import yield_strength
from physics.quantities import kelvin, metre, pascal
from physics.solid_mechanics.pressure_vessels import (
    THIN_WALL,
    LameCylinderStress,
    ThinWallCylinder,
    cylinder,
    lame_closed_cylinder,
)
from systems.contracts.results import (
    CalculationResult,
    ResultStatus,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import (
    failed_result,
    make_result,
    stage_guard,
)
from systems.stages.subsystems import run_cooling_stage, run_injector_stage

__all__ = (
    "run_cooling_stage",
    "run_injector_stage",
    "run_materials_stage",
    "run_structure_stage",
)


@stage_guard("materials")
def run_materials_stage(
    design: PropulsionDesign,
    *,
    material_id: str | None = None,
) -> CalculationResult:
    """Attach a Physics catalog material to the design (room-T handbook)."""

    stage_id = "materials"
    try:
        if material_id is None:
            material_id = design.subsystem_inputs.get("materials", {}).get("material_id") or str(
                (design.material_selection or {}).get("chamber_material_id") or ""
            )
        if not material_id:
            raise InsufficientDataError("An explicit chamber material ID is required.")
        material = get_material(material_id.lower())
        design.write_derived_slot(
            "material_selection",
            {
                "chamber_material_id": material.material_id,
                "condition": material.condition,
                "source": material.source,
            },
        )
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
            assumptions=(
                "Room-temperature handbook properties — not MMPDS allowables.",
            ),
            warnings=(
                "Validation: NOT_CLAIMED. Not a certified material allowables database.",
            ),
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
            inputs={"material_id": material_id},
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        return result


@stage_guard("structure")
def run_structure_stage(
    design: PropulsionDesign,
    *,
    wall_thickness_m: float | None = None,
    external_pressure: Quantity | None = None,
    external_pressure_source: str | None = None,
    material_temperature_k: float | None = None,
    pressure_model: str | None = None,
) -> CalculationResult:
    """Explicitly selected thin-wall or Lamé pressure-only preliminary screen."""

    stage_id = "structure"
    op = design.operating_point
    selected_id = (design.material_selection or {}).get("chamber_material_id")
    inputs: dict[str, object] = {"material_id": selected_id}
    model_id = THIN_WALL.model_id
    calculation_type = "structure.thin_wall"
    try:
        cfg = design.subsystem_inputs.get("structure", {})
        pressure_model = pressure_model or cfg.get("pressure_model", "THIN_WALL")
        if pressure_model not in {"THIN_WALL", "LAME_CLOSED_ENDS"}:
            raise InvalidInputError("Choose THIN_WALL or LAME_CLOSED_ENDS pressure stresses.")
        inputs["pressure_model"] = pressure_model
        if pressure_model == "LAME_CLOSED_ENDS":
            model_id = "PHYS-007.pressure_vessel.lame_closed_ends"
            calculation_type = "structure.lame_closed_ends"
        if op.chamber_pressure is None:
            raise InvalidInputError("structure requires chamber_pressure.")
        chamber = design.chamber_design or {}
        if "chamber_diameter_m" not in chamber:
            raise InvalidInputError(
                "structure requires chamber_diameter_m (run chamber)."
            )
        radius = 0.5 * validate_positive(
            float(chamber["chamber_diameter_m"]), "chamber_diameter_m"
        )
        saved = design.structural_design or {}
        if wall_thickness_m is None:
            wall_thickness_m = cfg.get("wall_thickness_m")
        if external_pressure is None and cfg.get("external_pressure_pa") is not None:
            external_pressure = pascal(cfg["external_pressure_pa"])
            external_pressure_source = cfg.get("external_pressure_source")
        if material_temperature_k is None:
            material_temperature_k = cfg.get("material_temperature_k")
        thickness = wall_thickness_m
        if thickness is None and "wall_thickness_m" in saved:
            thickness = float(saved["wall_thickness_m"])
        if thickness is None:
            raise InsufficientDataError("structure requires explicit wall_thickness_m.")
        thickness = validate_positive(thickness, "wall_thickness_m")
        if external_pressure is None and "external_pressure" in saved:
            external_pressure = Quantity.from_canonical_dict(saved["external_pressure"])
            external_pressure_source = str(saved.get("external_pressure_source") or "")
        if external_pressure is None:
            raise InsufficientDataError(
                "structure requires explicit external_pressure; ambient/jacket/coolant pressure is not inferred."
            )
        external_pressure_source = (
            external_pressure_source or "Explicit structural boundary input (user)."
        )
        # Core checks dimensions before any arithmetic; SI conversion is owned by Core.
        internal_si = op.chamber_pressure.convert_to(pascal(1).unit).to_si()
        external_si = external_pressure.convert_to(pascal(1).unit).to_si()
        if internal_si < 0 or external_si < 0:
            raise InvalidInputError(
                "Internal and external absolute pressures must be non-negative."
            )
        differential = pascal(internal_si - external_si)
        inputs.update(
            {
                "internal_pressure": op.chamber_pressure.to_canonical_dict(),
                "external_pressure": external_pressure.to_canonical_dict(),
                "external_pressure_source": external_pressure_source,
                "pressure_differential": differential.to_canonical_dict(),
                "radius_m": {"value": radius, "unit": "m"},
                "thickness_m": {"value": thickness, "unit": "m"},
            }
        )
        if differential.to_si() < 0:
            raise OutOfRangeError(
                "External pressure exceeds internal pressure; shell buckling is outside this tensile pressure-only screen."
            )
        if not selected_id:
            raise InsufficientDataError(
                "structure requires explicit material selection."
            )
        material = get_material(str(selected_id))
        if material_temperature_k is None and "material_temperature_k" in saved:
            material_temperature_k = float(saved["material_temperature_k"])
        if material_temperature_k is None:
            raise InsufficientDataError(
                "structure requires explicit material_temperature_k for catalog property validity."
            )
        inputs["material_temperature_k"] = {
            "value": material_temperature_k,
            "unit": "K",
        }
        extra_outputs = {}
        wall: ThinWallCylinder | LameCylinderStress
        if pressure_model == "LAME_CLOSED_ENDS":
            wall = lame_closed_cylinder(op.chamber_pressure, external_pressure, metre(radius), metre(thickness))
            governing = wall.von_mises
            extra_outputs = {"radial_stress_at_bore": wall.radial.to_canonical_dict(),
                             "von_mises_at_bore": wall.von_mises.to_canonical_dict()}
            assumptions = wall.identity.assumptions
            reference = "Lamé bore stresses; closed-end axial force balance; max von Mises at bore"
        else:
            wall = cylinder(differential, metre(radius), metre(thickness))
            if wall.radius_to_thickness < 10:
                raise OutOfRangeError("Thin-wall cylinder requires radius/thickness >= 10; no automatic model substitution.")
            governing = wall.hoop
            assumptions = ("Thin-wall membrane theory.",
                           "Uniform internal/external absolute pressures; tensile differential membrane load only.")
            reference = "hoop = (Pin - Pout) r / t; longitudinal = hoop/2"
        sy = yield_strength(material, kelvin(material_temperature_k)).require_valid()
        design.write_derived_slot(
            "structural_design",
            {
                "radius_m": radius,
                "wall_thickness_m": float(thickness),
                "external_pressure": external_pressure.to_canonical_dict(),
                "external_pressure_source": external_pressure_source,
                "pressure_differential_pa": differential.to_si(),
                "material_id": material.material_id,
                "material_temperature_k": material_temperature_k,
                "pressure_model": pressure_model,
                "stress_basis": "BORE_VON_MISES" if pressure_model == "LAME_CLOSED_ENDS" else "HOOP",
                "stress_over_yield": governing.to_si() / sy.to_si(),
                "hoop_stress_pa": wall.hoop.to_si(),
                "longitudinal_stress_pa": wall.longitudinal.to_si(),
                "yield_strength_pa": sy.to_si(),
                "hoop_over_yield": wall.hoop.to_si() / sy.to_si(),
            },
        )
        result = make_result(
            calculation_type=calculation_type,
            stage_id=stage_id,
            status=ResultStatus.CURRENT,
            model_id=model_id,
            model_version="0.1.0",
            inputs=inputs,
            outputs={
                **extra_outputs,
                "pressure_model": pressure_model,
                "stress_basis": "BORE_VON_MISES" if pressure_model == "LAME_CLOSED_ENDS" else "HOOP",
                "stress_over_yield": {"value": governing.to_si() / sy.to_si(), "unit": "1"},
                "hoop_stress": wall.hoop.to_canonical_dict(),
                "longitudinal_stress": wall.longitudinal.to_canonical_dict(),
                "yield_strength": sy.to_canonical_dict(),
                "material_id": {"value": material.material_id, "unit": "1"},
                "hoop_over_yield": {
                    "value": wall.hoop.to_si() / sy.to_si(),
                    "unit": "1",
                },
            },
            assumptions=(*assumptions,
                f"Yield is handbook typical at explicitly supplied {material_temperature_k:g} K.",
            ),
            warnings=("Not ASME/PED design. Validation: NOT_CLAIMED.",
                      "Smooth cylinder only: no cooling-channel ligaments, bimetallic interfaces, thermal stress, creep, fatigue, joints or nozzle loads.",
                      "An elastic stress calculation does not establish hardware readiness or an accepted design safety factor."),
            validity=ValidityInfo(status=ValidityState.VALID),
            verification=VerificationInfo(
                status="PASS",
                reference=reference,
            ),
            source=wall.identity.source,
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        design.workflow.invalidate_from(stage_id)
        design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
        design.workflow.results[stage_id].status = ResultStatus.CURRENT
        return result
    except Exception as exc:  # noqa: BLE001
        result = failed_result(
            calculation_type=calculation_type,
            stage_id=stage_id,
            exc=exc,
            model_id=model_id,
            inputs=inputs,
            out_of_range=isinstance(exc, OutOfRangeError),
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        return result
