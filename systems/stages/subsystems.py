"""Preliminary injector hydraulics and regenerative/gaseous-film cooling stages."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive
from physics.compressible_flow.bell_nozzle import NozzleFlowStation
from physics.exceptions import InsufficientDataError, OutOfRangeError
from physics.heat_transfer.bartz import BARTZ
from physics.heat_transfer.film_cooling import (
    FILM_COOLING,
)
from physics.heat_transfer.nozzle_profile import (
    GaseousSlotFilm,
    NozzleGasInputs,
    nozzle_wall_profile,
)
from physics.heat_transfer.regenerative import (
    REGENERATIVE,
    CoolingInputs,
    regenerative_cooling,
)
from physics.injectors.orifice import (
    LIQUID_ORIFICE,
    bipropellant_mass_split,
    liquid_orifice,
)
from physics.quantities import kelvin, metre, pascal
from physics.si import (
    UNIT_DYNAMIC_VISCOSITY,
    UNIT_SPECIFIC_HEAT,
    UNIT_THERMAL_CONDUCTIVITY,
)
from physics.thermochemistry.propellants import Phase, get_propellant_by_alias
from systems.contracts.results import (
    CalculationResult,
    ResultStatus,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import failed_result, make_result, stage_guard
from systems.stages.propellants import ensure_propellant_registry_loaded


def require_fields(config: dict[str, Any], fields: set[str]) -> None:
    missing = sorted(
        key for key in fields if config.get(key) is None or config.get(key) == ""
    )
    if missing:
        raise InsufficientDataError(
            "Explicit subsystem inputs required: " + ", ".join(missing)
        )


@stage_guard("injector")
def run_injector_stage(design: PropulsionDesign) -> CalculationResult:
    cfg = dict(design.subsystem_inputs.get("injector", {}))
    try:
        from systems.configuration.subsystems import SUBSYSTEM_FIELDS

        require_fields(cfg, SUBSYSTEM_FIELDS["injector"])
        registry_source = ensure_propellant_registry_loaded()
        selection = design.propellant_configuration
        for propellant_id in (selection.oxidizer_id, selection.fuel_id):
            if (
                not propellant_id
                or get_propellant_by_alias(propellant_id).phase is not Phase.LIQUID
            ):
                raise OutOfRangeError(
                    "Liquid-orifice sizing requires two liquid registry propellants; gas/supercritical flow needs a different model."
                )
        op = design.operating_point
        if (
            op.mass_flow is None
            or op.chamber_pressure is None
            or op.mixture_ratio is None
        ):
            raise InsufficientDataError(
                "Injector needs CURRENT performance mass flow, chamber pressure and O/F."
            )
        mdot = validate_positive(op.mass_flow.to_si(), "mass_flow")
        ratio = validate_positive(op.mixture_ratio, "mixture_ratio")
        oxidizer_flow, fuel_flow = bipropellant_mass_split(op.mass_flow, ratio)
        fuel = fuel_flow.to_si()
        streams = {}
        for name, flow in (("oxidizer", oxidizer_flow), ("fuel", fuel_flow)):
            sized = liquid_orifice(
                flow,
                Quantity(cfg[f"{name}_density_kg_m3"], SI.get("kg/m3")),
                pascal(cfg[f"{name}_pressure_drop_pa"]),
                Quantity(cfg[f"{name}_viscosity_pa_s"], UNIT_DYNAMIC_VISCOSITY),
                cfg[f"{name}_cd"],
                cfg[f"{name}_hole_count"],
            )
            streams[name] = {
                **asdict(sized),
                "pressure_drop_pa": cfg[f"{name}_pressure_drop_pa"],
                "manifold_pressure_pa": op.chamber_pressure.to_si()
                + cfg[f"{name}_pressure_drop_pa"],
                "pressure_drop_over_pc": cfg[f"{name}_pressure_drop_pa"]
                / op.chamber_pressure.to_si(),
            }
        outputs = {
            "oxidizer": streams["oxidizer"],
            "fuel": streams["fuel"],
            "mass_balance_residual_kg_s": streams["oxidizer"]["mass_flow_kg_s"]
            + fuel
            - mdot,
            "momentum_rate_ratio_ox_fuel": streams["oxidizer"]["momentum_rate_n"]
            / streams["fuel"]["momentum_rate_n"],
        }
        result = make_result(
            calculation_type="injector.liquid_orifice",
            stage_id="injector",
            status=ResultStatus.CURRENT,
            model_id=LIQUID_ORIFICE.model_id,
            model_version=LIQUID_ORIFICE.version,
            inputs={
                **cfg,
                "mass_flow": op.mass_flow.to_canonical_dict(),
                "mixture_ratio": ratio,
                "oxidizer_id": selection.oxidizer_id,
                "fuel_id": selection.fuel_id,
                "propellant_registry_source": registry_source,
                "performance_result_id": design.workflow.results[
                    "performance"
                ].result_id,
            },
            outputs=outputs,
            assumptions=LIQUID_ORIFICE.assumptions,
            warnings=LIQUID_ORIFICE.limitations
            + (
                "Single-phase liquid properties and Cd are user-supplied; cavitation/stability NOT_ASSESSED.",
            ),
            validity=ValidityInfo(
                status=ValidityState.UNKNOWN, valid_range=LIQUID_ORIFICE.validity_range
            ),
            verification=VerificationInfo(
                status="SOFTWARE_VERIFIED", reference=LIQUID_ORIFICE.verification_status
            ),
            source=LIQUID_ORIFICE.source,
            design_revision=design.revision,
        )
        design.write_derived_slot("injector_design", outputs)
    except Exception as exc:  # noqa: BLE001
        result = failed_result(
            calculation_type="injector.liquid_orifice",
            stage_id="injector",
            exc=exc,
            model_id=LIQUID_ORIFICE.model_id,
            inputs=cfg,
            design_revision=design.revision,
            out_of_range=isinstance(exc, OutOfRangeError),
        )
    design.store_stage_result("injector", result)
    return result


def _coolant_inputs(cfg: dict[str, Any]) -> CoolingInputs:
    mapping = {
        "mass_flow": ("coolant_mass_flow_kg_s", SI.get("kg/s")),
        "inlet_temperature": ("inlet_temperature_k", SI.get("K")),
        "inlet_pressure": ("inlet_pressure_pa", SI.get("Pa")),
        "density": ("density_kg_m3", SI.get("kg/m3")),
        "viscosity": ("viscosity_pa_s", UNIT_DYNAMIC_VISCOSITY),
        "conductivity": ("conductivity_w_m_k", UNIT_THERMAL_CONDUCTIVITY),
        "specific_heat": ("cp_j_kg_k", UNIT_SPECIFIC_HEAT),
        "channel_width": ("channel_width_m", SI.get("m")),
        "channel_depth": ("channel_depth_m", SI.get("m")),
        "rib_width": ("rib_width_m", SI.get("m")),
        "wall_thickness": ("wall_thickness_m", SI.get("m")),
        "wall_conductivity": ("wall_conductivity_w_m_k", UNIT_THERMAL_CONDUCTIVITY),
        "min_temperature": ("min_temperature_k", SI.get("K")),
        "max_temperature": ("max_temperature_k", SI.get("K")),
        "max_wall_temperature": ("max_wall_temperature_k", SI.get("K")),
        "max_vapour_pressure": ("max_vapour_pressure_pa", SI.get("Pa")),
    }
    require_fields(
        cfg,
        {field for field, _unit in mapping.values()}
        | {"channel_count", "direction", "property_source", "film_mode"},
    )
    values = {
        name: Quantity(cfg[field], unit) for name, (field, unit) in mapping.items()
    }
    return CoolingInputs(
        **values, channel_count=cfg["channel_count"], direction=cfg["direction"]
    )


@stage_guard("cooling")
def run_cooling_stage(design: PropulsionDesign) -> CalculationResult:
    cfg = dict(design.subsystem_inputs.get("cooling", {}))
    try:
        coolant = _coolant_inputs(cfg)
        contour = design.workflow.current_result("nozzle")
        if contour is None or not contour.outputs.get("stations"):
            raise InsufficientDataError(
                "Generate a CURRENT bell contour before regenerative cooling."
            )
        rows = tuple(NozzleFlowStation(**row) for row in contour.outputs["stations"])
        op, gas = design.operating_point, design.thermal_design or {}
        require_fields(
            gas,
            {"viscosity_pa_s", "conductivity_w_m_k", "cp_j_kg_k", "wall_temperature_k"},
        )
        if (
            op.chamber_pressure is None
            or op.characteristic_velocity is None
            or op.chamber_temperature is None
            or op.gamma is None
            or op.mass_flow is None
        ):
            raise InsufficientDataError(
                "Cooling requires CURRENT operating-point and thermal boundary inputs."
            )
        gas_inputs = NozzleGasInputs(
            op.chamber_pressure,
            op.chamber_temperature,
            op.gamma,
            op.characteristic_velocity,
            op.mass_flow,
            Quantity(gas["viscosity_pa_s"], UNIT_DYNAMIC_VISCOSITY),
            Quantity(gas["conductivity_w_m_k"], UNIT_THERMAL_CONDUCTIVITY),
            Quantity(gas["cp_j_kg_k"], UNIT_SPECIFIC_HEAT),
            kelvin(gas["wall_temperature_k"]),
            metre(contour.outputs["throat_curvature_radius_m"]),
        )
        mode = cfg["film_mode"]
        if mode not in {"none", "gaseous_slot"}:
            raise InvalidInputError(
                "film_mode must be none or gaseous_slot; liquid films are not implemented."
            )
        film = None
        if mode == "gaseous_slot":
            film_fields = {
                "film_slot_x_m",
                "film_slot_height_m",
                "film_blowing_ratio",
                "film_temperature_k",
                "film_cp_j_kg_k",
                "film_delta0_m",
                "film_delta_growth_rate",
                "film_valid_length_m",
                "film_source",
            }
            require_fields(cfg, film_fields)
            film = GaseousSlotFilm(
                metre(cfg["film_slot_x_m"]),
                metre(cfg["film_slot_height_m"]),
                cfg["film_blowing_ratio"],
                kelvin(cfg["film_temperature_k"]),
                Quantity(cfg["film_cp_j_kg_k"], UNIT_SPECIFIC_HEAT),
                metre(cfg["film_delta0_m"]),
                cfg["film_delta_growth_rate"],
                metre(cfg["film_valid_length_m"]),
            )
        profile, film_flow = nozzle_wall_profile(rows, gas_inputs, film)
        evaluated = regenerative_cooling(profile, coolant)
        outputs = asdict(evaluated)
        outputs["segments"] = [asdict(row) for row in evaluated.segments]
        outputs["coverage"] = "divergent_nozzle_only"
        outputs["max_hot_wall_temperature_k"] = max(
            row.peak_hot_wall_temperature_k for row in evaluated.segments
        )
        outputs["film_mass_flow_estimate_kg_s"] = film_flow
        outputs["film_model"] = (
            FILM_COOLING.model_id if mode == "gaseous_slot" else "DISABLED_EXPLICITLY"
        )
        outputs["model_identities"] = {
            "regenerative": REGENERATIVE.to_canonical_dict(),
            "film": FILM_COOLING.to_canonical_dict() if film is not None else None,
        }
        warnings = (
            *REGENERATIVE.limitations,
            "Gas profile: existing SI Bartz correlation scaled by (At/A)^0.9; recovery Taw is computed from Pr, not set equal to Tc.",
            "Gas h is frozen at the explicit thermal-stage wall-temperature assumption, not iterated with the predicted wall.",
            "Coolant and film flow are explicitly specified streams, not deducted from Performance; cycle/mixture/heat-loss coupling remains open.",
        )
        if mode == "gaseous_slot":
            warnings += (
                *FILM_COOLING.limitations,
                "Boundary layer uses the user-sourced linear thickness profile; acceleration applicability is NOT_VALIDATED.",
            )
        result = make_result(
            calculation_type="cooling.regenerative_film",
            stage_id="cooling",
            status=ResultStatus.CURRENT,
            model_id=REGENERATIVE.model_id,
            model_version=REGENERATIVE.version,
            inputs={
                **cfg,
                "nozzle_result_id": contour.result_id,
                "thermal_result_id": design.workflow.results["thermal"].result_id,
                "gas_properties": gas,
                "gas_model_id": BARTZ.model_id,
            },
            outputs=outputs,
            assumptions=REGENERATIVE.assumptions,
            warnings=warnings,
            validity=ValidityInfo(
                status=ValidityState.UNKNOWN, valid_range=REGENERATIVE.validity_range
            ),
            verification=VerificationInfo(
                status="SOFTWARE_VERIFIED", reference=REGENERATIVE.verification_status
            ),
            source=REGENERATIVE.source,
            design_revision=design.revision,
        )
        design.write_derived_slot("cooling_design", outputs)
    except Exception as exc:  # noqa: BLE001
        result = failed_result(
            calculation_type="cooling.regenerative_film",
            stage_id="cooling",
            exc=exc,
            model_id=REGENERATIVE.model_id,
            inputs=cfg,
            design_revision=design.revision,
            out_of_range=isinstance(exc, OutOfRangeError),
        )
    design.store_stage_result("cooling", result)
    return result
