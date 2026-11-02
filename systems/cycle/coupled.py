"""Immutable selected-cycle assessment over actual saved subsystem results.

This downstream service never promotes or rewrites the upstream workflow.
"""

from __future__ import annotations

import json
import math
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from typing import Any

from core.dimension import FORCE, MASS_FLOW_RATE, PRESSURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.exceptions import InsufficientDataError, OutOfRangeError
from physics.feed.gas_generator import (
    GAS_GENERATOR,
    LiquidPump,
    Turbine,
    efficiency,
    solve_power_balance,
)
from physics.injectors.orifice import bipropellant_mass_split
from physics.si import UNIT_SPECIFIC_ENERGY, UNIT_SPECIFIC_HEAT
from systems.contracts.results import (
    CalculationResult,
    ProvenanceInfo,
    ResultStatus,
    ValidationInfo,
    VerificationInfo,
)
from systems.cycle.pressure_fed import _keys, _number, _retained_quantity, _source
from systems.projects.models import PropulsionDesign

INPUT_SCHEMA = "cosmos.coupled-cycle-input.v1"
OUTPUT_SCHEMA = "cosmos.coupled-cycle.v1"
STREAM_UNITS = {
    "density": "kg/m3",
    "inlet_pressure": "Pa",
    "outlet_pressure": "Pa",
    "core_loss": "Pa",
    "core_control_drop": "Pa",
    "gg_loss": "Pa",
    "gg_control_drop": "Pa",
    "external_flow": "kg/s",
    "external_sink_pressure": "Pa",
    "external_loss": "Pa",
    "external_control_drop": "Pa",
}
GG_UNITS = {
    "temperature": "K",
    "inlet_pressure": "Pa",
    "outlet_pressure": "Pa",
    "cp": "J/kg/K",
    "inlet_specific_enthalpy": "J/kg",
    "net_released_energy": "J/kg",
    "heat_loss": "W",
    "auxiliary_power": "W",
    "maximum_flow": "kg/s",
}


def q(
    value: Any, unit: str, name: str, *, signed: bool = False, zero: bool = False
) -> Quantity:
    _keys(value, {"value", "unit"}, name)
    if value["unit"] != unit:
        raise InvalidInputError(f"{name} requires explicit SI unit {unit}.")
    number = _number(value["value"], name)
    if not signed and (number < 0 or (number == 0 and not zero)):
        raise InvalidInputError(f"{name} is outside its sign domain.")
    native = {"J/kg": UNIT_SPECIFIC_ENERGY, "J/kg/K": UNIT_SPECIFIC_HEAT}.get(unit)
    return Quantity(number, native if native is not None else SI.get(unit))


def validate(spec: dict[str, Any]) -> dict[str, Any]:
    _keys(
        spec,
        {
            "schema",
            "cycle_type",
            "regime",
            "cooling_mode",
            "film",
            "streams",
            "gas_generator",
            "pressure_tolerance",
            "mass_flow_tolerance",
            "power_tolerance",
        },
        "cycle specification",
    )
    if spec["schema"] != INPUT_SCHEMA or spec["regime"] != "STEADY_DESIGN_POINT":
        raise OutOfRangeError(
            "Require supported schema and STEADY_DESIGN_POINT regime."
        )
    if spec["cycle_type"] not in {"GAS_GENERATOR", "PRESSURE_FED"}:
        raise OutOfRangeError(
            "Only selected pressure-fed and open gas-generator assessments are supported."
        )
    if spec["cooling_mode"] not in {"NONE_EXPLICIT", "FUEL_CORE_SERIES"}:
        raise OutOfRangeError(
            "Explicitly disable cooling or select full-core-fuel series cooling."
        )
    parsed: dict[str, Any] = {
        name: q(spec[name], unit, name).to_si()
        for name, unit in (
            ("pressure_tolerance", "Pa"),
            ("mass_flow_tolerance", "kg/s"),
            ("power_tolerance", "W"),
        )
    }
    _keys(spec["streams"], {"oxidizer", "fuel"}, "streams")
    for name, cfg in spec["streams"].items():
        _keys(cfg, {*STREAM_UNITS, "phase", "efficiency", "source"}, name)
        if cfg["phase"] != "LIQUID":
            raise OutOfRangeError(
                "Pump/feed boundaries require explicit single-phase LIQUID declarations."
            )
        _source(cfg["source"], name + " properties/pressure/loss applicability")
        row = {
            key: q(
                cfg[key],
                unit,
                name + "." + key,
                zero=key
                not in {
                    "density",
                    "inlet_pressure",
                    "outlet_pressure",
                    "external_sink_pressure",
                },
            ).to_si()
            for key, unit in STREAM_UNITS.items()
        }
        if spec["cycle_type"] == "GAS_GENERATOR":
            row["efficiency"] = efficiency(
                _number(cfg["efficiency"], "pump efficiency"), "pump efficiency"
            )
        elif (
            cfg["efficiency"] is not None
            or row["inlet_pressure"] != row["outlet_pressure"]
            or row["gg_loss"] != 0
            or row["gg_control_drop"] != 0
        ):
            raise InvalidInputError(
                "Pump-free feed requires null efficiency, identical source/discharge pressure and explicit zero GG losses."
            )
        parsed[name] = row
    gg = spec["gas_generator"]
    if spec["cycle_type"] == "GAS_GENERATOR":
        _keys(
            gg,
            {
                *GG_UNITS,
                "mixture_ratio",
                "gamma",
                "turbine_efficiency",
                "shaft_efficiency",
                "source",
            },
            "gas_generator",
        )
        _source(gg["source"], "GG gas state/efficiencies/common-reference enthalpies")
        parsed["gg"] = {
            key: q(
                gg[key],
                unit,
                "GG." + key,
                signed=key == "inlet_specific_enthalpy",
                zero=key in {"net_released_energy", "heat_loss", "auxiliary_power"},
            ).to_si()
            for key, unit in GG_UNITS.items()
        }
        for key in ("mixture_ratio", "gamma", "turbine_efficiency", "shaft_efficiency"):
            parsed["gg"][key] = _number(gg[key], "GG." + key)
    elif gg is not None:
        raise InvalidInputError("Pressure-fed gas_generator must explicitly be null.")
    if spec["film"] is not None:
        _keys(
            spec["film"],
            {"boundary", "sink_pressure", "loss", "control_drop", "source"},
            "film",
        )
        if spec["film"]["boundary"] != "EXTERNALLY_CONDITIONED_FUEL":
            raise OutOfRangeError(
                "Only explicitly externally conditioned additional fuel film is supported; no phase-change model."
            )
        _source(spec["film"]["source"], "film conditioner/pressure boundary")
        parsed["film"] = {
            key: q(
                spec["film"][key], "Pa", "film." + key, zero=key != "sink_pressure"
            ).to_si()
            for key in ("sink_pressure", "loss", "control_drop")
        }
    return parsed


def assess(
    design: PropulsionDesign, specification: dict[str, Any]
) -> CalculationResult:
    spec = deepcopy(specification)
    values = validate(spec)
    text = design.to_canonical_json()
    snapshot = PropulsionDesign.from_canonical_dict(json.loads(text))
    if (
        snapshot.cycle_configuration.cycle_type.value != spec["cycle_type"]
        or snapshot.requirements.cycle_type != spec["cycle_type"]
    ):
        raise InvalidInputError(
            "Select the same explicit cycle in the saved baseline and assessment."
        )
    sources: dict[str, CalculationResult] = {}

    def source(stage: str) -> CalculationResult:
        result = snapshot.workflow.current_result(stage)
        if (
            result is None
            or snapshot.workflow.graph.get(stage).status is not ResultStatus.CURRENT
        ):
            raise InsufficientDataError(
                f"CURRENT retained {stage} result/graph required."
            )
        sources[stage] = result
        return result

    op, props, thermo, performance, injector = (
        source(key)
        for key in (
            "operating_point",
            "propellants",
            "thermochemistry",
            "performance",
            "injector",
        )
    )
    expected_type = (
        "performance.cea_ideal_nozzle"
        if thermo.inputs.get("engine") == "nasa/cea"
        else "performance.choked_nozzle_thrust"
    )
    # CEA uses its own output mass flow; never substitute perfect-gas mdot.
    if performance.calculation_type != expected_type:
        raise InvalidInputError(
            "Retained performance adapter does not match thermochemistry."
        )
    if (snapshot.thermochemistry_configuration.get("mode") == "nasa_cea") != (
        thermo.inputs.get("engine") == "nasa/cea"
    ):
        raise InvalidInputError(
            "CEA configuration/source mismatch; no assumed-state fallback."
        )
    if (
        expected_type == "performance.cea_ideal_nozzle"
        and performance.inputs.get("thermochemistry_result_id") != thermo.result_id
    ):
        raise InvalidInputError(
            "CEA performance references a different thermochemistry result."
        )
    pc = _retained_quantity(
        performance.inputs.get("chamber_pressure"), PRESSURE, "performance Pc"
    ).to_si()
    total_q = _retained_quantity(
        performance.outputs.get("mass_flow"), MASS_FLOW_RATE, "core mass flow"
    )
    thrust = _retained_quantity(
        performance.outputs.get("thrust"), FORCE, "core thrust"
    ).to_si()
    ratio = _number(op.outputs.get("mixture_ratio"), "core O/F")
    if (
        ratio <= 0
        or _retained_quantity(
            op.outputs.get("chamber_pressure"), PRESSURE, "operating Pc"
        ).to_si()
        != pc
        or snapshot.requirements.mixture_ratio != ratio
        or snapshot.propellant_configuration.mixture_ratio != ratio
        or props.inputs.get("mixture_ratio") != ratio
        or snapshot.requirements.target_chamber_pressure is None
        or snapshot.requirements.target_chamber_pressure.to_si() != pc
        or snapshot.operating_point.chamber_pressure is None
        or snapshot.operating_point.chamber_pressure.to_si() != pc
        or snapshot.operating_point.mixture_ratio != ratio
    ):
        raise InvalidInputError("Retained core pressure/O/F context is inconsistent.")
    for name in ("oxidizer", "fuel"):
        if props.inputs.get(name + "_id") != getattr(
            snapshot.propellant_configuration, name + "_id"
        ):
            raise InvalidInputError("Retained propellant identity mismatch.")
    if injector.inputs.get("performance_result_id") != performance.result_id:
        raise InvalidInputError(
            "Injector was not sized against the retained performance result."
        )
    core = dict(
        zip(
            ("oxidizer", "fuel"),
            (v.to_si() for v in bipropellant_mass_split(total_q, ratio)),
            strict=True,
        )
    )
    mt, pt, wt = (
        values[key]
        for key in ("mass_flow_tolerance", "pressure_tolerance", "power_tolerance")
    )
    rows: list[dict[str, Any]] = []

    def residual(name: str, value: float, tolerance: float, unit: str) -> None:
        if not math.isfinite(value):
            raise InvalidInputError(f"Nonfinite residual: {name}.")
        rows.append(
            {
                "name": name,
                "value": value,
                "unit": unit,
                "tolerance": tolerance,
                "passed": abs(value) <= tolerance,
            }
        )

    for name, core_flow in core.items():
        row = injector.outputs[name]
        residual(
            name + ".injector_mass",
            _number(row["mass_flow_kg_s"], "injector flow") - core_flow,
            mt,
            "kg/s",
        )
        residual(
            name + ".injector_pressure",
            _number(row["manifold_pressure_pa"], "injector manifold")
            - pc
            - _number(row["pressure_drop_pa"], "injector dp"),
            pt,
            "Pa",
        )
        if (
            _number(injector.inputs[name + "_density_kg_m3"], "injector density")
            != values[name]["density"]
        ):
            raise InvalidInputError(
                "Injector and feed density assumptions differ; rerun with consistent sourced properties."
            )

    cooling_loss = heat = film_flow = 0.0
    cooling_record: dict[str, Any] | None = None
    if spec["cooling_mode"] == "FUEL_CORE_SERIES" or spec["film"] is not None:
        cooling = source("cooling")
        # Retain and verify exact nozzle/thermal dependency identities as well.
        if (
            cooling.inputs.get("nozzle_result_id") != source("nozzle").result_id
            or cooling.inputs.get("thermal_result_id") != source("thermal").result_id
        ):
            raise InvalidInputError(
                "Cooling dependency identity does not match the retained nozzle/thermal results."
            )
        if spec["cooling_mode"] == "FUEL_CORE_SERIES":
            cfg, out = cooling.inputs, cooling.outputs
            residual(
                "cooling.core_fuel_flow",
                _number(cfg["coolant_mass_flow_kg_s"], "coolant flow") - core["fuel"],
                mt,
                "kg/s",
            )
            if (
                _number(cfg["density_kg_m3"], "coolant density")
                != values["fuel"]["density"]
            ):
                raise InvalidInputError("Coolant and fuel density assumptions differ.")
            cooling_loss = _number(
                out["total_pressure_loss_pa"], "cooling pressure loss"
            )
            heat = _number(out["total_heat_w"], "cooling heat")
            if cooling_loss < 0 or heat < 0:
                raise InvalidInputError(
                    "Heating model requires nonnegative heat pickup/pressure loss."
                )
            residual(
                "cooling.inlet_pressure",
                _number(cfg["inlet_pressure_pa"], "cooling inlet")
                - values["fuel"]["outlet_pressure"],
                pt,
                "Pa",
            )
            residual(
                "cooling.pressure",
                _number(cfg["inlet_pressure_pa"], "cooling inlet")
                - _number(out["outlet_pressure_pa"], "cooling outlet")
                - cooling_loss,
                pt,
                "Pa",
            )
            residual(
                "cooling.energy",
                heat
                - core["fuel"]
                * _number(cfg["cp_j_kg_k"], "coolant cp")
                * (
                    _number(out["outlet_temperature_k"], "coolant outlet T")
                    - _number(cfg["inlet_temperature_k"], "coolant inlet T")
                ),
                wt,
                "W",
            )
            cooling_record = {
                "source_result_id": cooling.result_id,
                "heat_pickup_w": heat,
                "pressure_loss_pa": cooling_loss,
                "flow_kg_s": core["fuel"],
                "routing": "RETURN_TO_CORE_FUEL_NO_DOUBLE_COUNT",
                "outlet_temperature_k": out["outlet_temperature_k"],
            }
        film_flow = _number(
            cooling.outputs["film_mass_flow_estimate_kg_s"], "retained film flow"
        )
        if film_flow < 0:
            raise InvalidInputError("Film flow must be nonnegative.")
        if spec["film"] is None and film_flow != 0:
            raise InvalidInputError(
                "A nonzero retained film stream requires explicit additional fuel routing and conditioner boundary."
            )
        if spec["film"] is not None and (
            film_flow <= 0 or cooling.inputs.get("film_mode") != "gaseous_slot"
        ):
            raise InvalidInputError(
                "Enabled film requires an actual CURRENT gaseous-slot cooling result with positive film flow."
            )
    elif snapshot.workflow.current_result("cooling") is not None:
        cooling = source("cooling")
        if _number(cooling.outputs["film_mass_flow_estimate_kg_s"], "film flow") != 0:
            raise InvalidInputError(
                "Cannot silently discard existing nonzero film; select its explicit boundary."
            )

    base = {
        name: math.fsum(
            (
                core[name],
                values[name]["external_flow"],
                film_flow if name == "fuel" else 0,
            )
        )
        for name in core
    }
    gg_flow = {"oxidizer": 0.0, "fuel": 0.0}
    power: dict[str, Any] | None = None
    if spec["cycle_type"] == "GAS_GENERATOR":
        gg = values["gg"]
        pump = {
            name: LiquidPump(
                q(spec["streams"][name]["density"], "kg/m3", "density"),
                q(spec["streams"][name]["inlet_pressure"], "Pa", "pin"),
                q(spec["streams"][name]["outlet_pressure"], "Pa", "pout"),
                values[name]["efficiency"],
            )
            for name in core
        }
        turbine = Turbine(
            q(spec["gas_generator"]["temperature"], "K", "Tt"),
            q(spec["gas_generator"]["inlet_pressure"], "Pa", "Pt in"),
            q(spec["gas_generator"]["outlet_pressure"], "Pa", "Pt out"),
            q(spec["gas_generator"]["cp"], "J/kg/K", "cp"),
            gg["gamma"],
            gg["turbine_efficiency"],
            gg["shaft_efficiency"],
        )
        solved = solve_power_balance(
            oxidizer_base_flow=Quantity(base["oxidizer"], SI.get("kg/s")),
            fuel_base_flow=Quantity(base["fuel"], SI.get("kg/s")),
            oxidizer_pump=pump["oxidizer"],
            fuel_pump=pump["fuel"],
            turbine=turbine,
            gg_mixture_ratio=gg["mixture_ratio"],
            auxiliary_power=Quantity(gg["auxiliary_power"], SI.get("W")),
            maximum_gg_flow=Quantity(gg["maximum_flow"], SI.get("kg/s")),
        )
        power = asdict(solved)
        gg_flow = {
            "oxidizer": solved.gg_oxidizer_flow_kg_s,
            "fuel": solved.gg_fuel_flow_kg_s,
        }
        residual("shaft.power", solved.shaft_residual_w, wt, "W")
        residual("turbine.energy", solved.turbine_energy_residual_w, wt, "W")
        residual(
            "GG.energy",
            solved.gg_mass_flow_kg_s
            * (
                gg["inlet_specific_enthalpy"]
                + gg["net_released_energy"]
                - gg["cp"] * gg["temperature"]
            )
            - gg["heat_loss"],
            wt,
            "W",
        )
        residual(
            "GG.mass", solved.gg_mass_flow_kg_s - sum(gg_flow.values()), mt, "kg/s"
        )
    streams = {}
    for name, core_flow in core.items():
        cfg = values[name]
        withdrawal = base[name] + gg_flow[name]
        residual(
            name + ".mass",
            math.fsum(
                (
                    withdrawal,
                    -core_flow,
                    -gg_flow[name],
                    -cfg["external_flow"],
                    -film_flow if name == "fuel" else 0,
                )
            ),
            mt,
            "kg/s",
        )
        required = (
            injector.outputs[name]["manifold_pressure_pa"]
            + cfg["core_loss"]
            + cfg["core_control_drop"]
            + (cooling_loss if name == "fuel" else 0)
        )
        residual(name + ".core_pressure", cfg["outlet_pressure"] - required, pt, "Pa")
        if power is not None:
            residual(
                name + ".GG_pressure",
                cfg["outlet_pressure"]
                - values["gg"]["inlet_pressure"]
                - cfg["gg_loss"]
                - cfg["gg_control_drop"],
                pt,
                "Pa",
            )
        if cfg["external_flow"] > 0:
            residual(
                name + ".external_pressure",
                cfg["outlet_pressure"]
                - cfg["external_sink_pressure"]
                - cfg["external_loss"]
                - cfg["external_control_drop"],
                pt,
                "Pa",
            )
        streams[name] = {
            "core_flow_kg_s": core_flow,
            "gg_flow_kg_s": gg_flow[name],
            "film_flow_kg_s": film_flow if name == "fuel" else 0.0,
            "external_flow_kg_s": cfg["external_flow"],
            "withdrawal_kg_s": withdrawal,
            "inlet_pressure_pa": cfg["inlet_pressure"],
            "outlet_pressure_pa": cfg["outlet_pressure"],
            "required_core_pressure_pa": required,
        }
    if film_flow > 0:
        residual(
            "film.pressure",
            values["fuel"]["outlet_pressure"]
            - values["film"]["sink_pressure"]
            - values["film"]["loss"]
            - values["film"]["control_drop"],
            pt,
            "Pa",
        )
    withdrawal_total = math.fsum(row["withdrawal_kg_s"] for row in streams.values())
    if not math.isfinite(withdrawal_total) or withdrawal_total <= 0:
        raise InvalidInputError("Total withdrawal exceeds finite range.")
    closed = all(row["passed"] for row in rows)
    return CalculationResult(
        calculation_type="cycle.selected.coupled_assessment",
        model_id=GAS_GENERATOR.model_id if power else "PHYS.feed.coupled_pressure_fed",
        model_version=GAS_GENERATOR.version,
        status=ResultStatus.CURRENT,
        stage_id=None,
        design_revision=snapshot.revision,
        inputs={
            "specification": spec,
            "baseline_canonical_text": text,
            "baseline_sha256": sha256(text.encode()).hexdigest(),
            "source_results": {
                key: result.to_canonical_dict() for key, result in sources.items()
            },
        },
        outputs={
            "schema": OUTPUT_SCHEMA,
            "cycle_type": spec["cycle_type"],
            "assessment_status": "BALANCED_DECLARED_DESIGN_POINT"
            if closed
            else "UNBALANCED",
            "assessment_balances_closed_within_declared_tolerances": closed,
            "streams": streams,
            "residuals": rows,
            "power": power,
            "shaft_power_status": "CALCULATED" if power else "NOT_APPLICABLE",
            "cooling": cooling_record,
            "film_boundary": spec["film"],
            "core_thrust_n": thrust,
            "core_mass_flow_kg_s": total_q.to_si(),
            "total_withdrawal_kg_s": withdrawal_total,
            "total_withdrawal_mixture_ratio": streams["oxidizer"]["withdrawal_kg_s"]
            / streams["fuel"]["withdrawal_kg_s"],
            "core_only_thrust_effective_isp_s": thrust / withdrawal_total / 9.80665,
            "core_performance_adapter": expected_type,
            "workflow_cycle_complete": False,
            "physical_validation": "NOT_PERFORMED",
            "pressurant": "IMPOSED_BOUNDARY_NOT_SIZED",
            "film_conditioner": "EXTERNAL_BOUNDARY_NOT_SOLVED",
            "core_thermal_feedback": "FROZEN_CORE_NOT_RECOMPUTED",
            "scope": "Steady prescribed-component design-point assessment, not a map/speed/full-network operating-point solver",
        },
        assumptions=GAS_GENERATOR.assumptions,
        warnings=(
            *GAS_GENERATOR.limitations,
            "Regenerative heat/film effects are consumed from the retained thermal model; core combustion/nozzle heat-loss feedback is not recalculated. No additional exhaust thrust is credited.",
        ),
        verification=VerificationInfo(status="SOFTWARE_VERIFIED_DECLARED_MODEL"),
        validation=ValidationInfo(status="NOT_PERFORMED"),
        provenance=ProvenanceInfo(
            source=GAS_GENERATOR.source,
            model="Selected steady component-boundary assessment",
            version=GAS_GENERATOR.version,
        ),
    )
