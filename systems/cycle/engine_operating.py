"""Solve selected feed/shaft/nozzle operating point with two-way regenerative HP feedback.

Immutable downstream candidate only: no writes into the frozen workflow.
All original sizing/CEA/calculation modules remain unchanged.
"""

from __future__ import annotations

import json
import math
from copy import deepcopy
from dataclasses import asdict
from itertools import pairwise
from typing import Any

import numpy as np

from core.exceptions import CosmosError, InvalidInputError, SolverConvergenceError
from numerics.nonlinear_solver.bounded import solve
from physics.compressible_flow.heated_nozzle import HEATED_NOZZLE, nonadiabatic_nozzle
from physics.exceptions import InsufficientDataError, OutOfRangeError
from physics.feed.characteristics import (
    liquid_enthalpy_increment,
    pressure_loss,
    pump_state,
)
from physics.feed.gas_generator import Turbine
from physics.heat_transfer.bartz import bartz_heat_transfer_coefficient
from physics.heat_transfer.pressure_cooling import pressure_coupled_cooling
from physics.heat_transfer.regenerative import (
    CoolingInputs,
    GasWallStation,
)
from physics.validity import ValidityStatus
from plugins.nasa_cea.chamber import ChamberState, NasaHPChamber
from systems.contracts.results import (
    CalculationResult,
    ProvenanceInfo,
    ResultStatus,
    ValidationInfo,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.cycle.operating_contract import CORE_UNKNOWNS, GG_UNKNOWNS, validate
from systems.cycle.operating_contract import quantity as q
from systems.projects.models import PropulsionDesign


class ThermalNotConverged(SolverConvergenceError):
    def __init__(self, history: list[dict[str, Any]]):
        super().__init__("THERMAL_MAX_ITERATIONS: gas/wall/coolant/CEA fixed point not converged; no solved state.")
        self.history = deepcopy(history)


def _chamber(chamber: NasaHPChamber, pc: float, ox: float, fuel: float, added: float) -> ChamberState:
    return chamber.solve(q(pc, "Pa"), ox / fuel, q(added, "J/kg"))


def _nozzle(pc: float, gas: ChamberState, areas: list[float], heat: list[float]):
    return nonadiabatic_nozzle(q(pc, "Pa"), q(gas.temperature_k, "K"), q(gas.cp_j_kg_k, "J/kg/K"), q(gas.gas_constant_j_kg_k, "J/kg/K"), tuple(q(a, "m2") for a in areas), tuple(q(v, "W") for v in heat))


def _thermal(
    chamber: NasaHPChamber, pc: float, ox: float, fuel: float, base_h: float,
    fuel_pressure: float, fuel_temperature: float,
    rows: list[dict[str, Any]], cfg: dict[str, Any], values: dict[str, Any],
) -> dict[str, Any]:
    geometry = [(float(row["x_m"]), float(row["radius_m"])) for row in rows]
    areas = [math.pi * radius**2 for _, radius in geometry]
    policy, feed = values["cooling"], values["fuel"]
    heat = [0.] * (len(rows) - 1)
    wall = [policy["wall_initial_temperature"]] * len(rows)
    history = []
    for iteration in range(policy["max_iterations"]):
        gas = _chamber(chamber, pc, ox, fuel, base_h + math.fsum(heat) / (ox + fuel))
        nozzle = _nozzle(pc, gas, areas, heat)
        if any(not policy["gas_min_temperature"] <= station.temperature_k <= policy["gas_max_temperature"] for station in nozzle.stations):
            raise OutOfRangeError("Gas state outside explicitly supplied frozen-property temperature window.")
        if policy["mode"] == "NONE_EXPLICIT":
            return {"gas": gas, "nozzle": nozzle, "cooling": None, "heat_extraction_w": heat, "thermal_history": [{"iteration": 0, "termination": "COOLING_EXPLICITLY_DISABLED"}], "heat_coupling_residual_w": 0.}
        profile = []
        gamma = gas.cp_j_kg_k / (gas.cp_j_kg_k - gas.gas_constant_j_kg_k)
        pr = gas.cp_j_kg_k * gas.viscosity_pa_s / gas.conductivity_w_m_k
        for index, (station, (x, radius)) in enumerate(zip(nozzle.stations, geometry, strict=True)):
            taw = station.temperature_k * (1 + pr**(1 / 3) * (gamma - 1) / 2 * station.mach**2)
            bartz = bartz_heat_transfer_coefficient(
                q(2 * geometry[0][1], "m"), q(gas.viscosity_pa_s, "Pa*s"), q(gas.conductivity_w_m_k, "W/m/K"), q(gas.cp_j_kg_k, "J/kg/K"),
                q(pc, "Pa"), q(pc * areas[0] / nozzle.mass_flow_kg_s, "m/s"), station.mach, gamma,
                q(wall[index], "K"), q(taw, "K"),
            )
            if bartz.validity is not ValidityStatus.VALID:
                raise OutOfRangeError("Bartz gas-side Reynolds window exceeded.")
            h = bartz.heat_transfer_coefficient.to_si() * (areas[0] / station.area_m2)**.9
            profile.append(GasWallStation(q(x, "m"), q(radius, "m"), q(h, "W/m2/K"), q(taw, "K")))
        # Only immutable channel/wall geometry is reused. New liquid states and
        # sourced properties are recalculated at the candidate flow/pressure.
        cooling = pressure_coupled_cooling(tuple(profile), CoolingInputs(
            mass_flow=q(fuel, "kg/s"), inlet_temperature=q(fuel_temperature, "K"), inlet_pressure=q(fuel_pressure, "Pa"),
            density=q(feed["density"], "kg/m3"), viscosity=q(feed["viscosity"], "Pa*s"), conductivity=q(feed["conductivity"], "W/m/K"), specific_heat=q(feed["cp"], "J/kg/K"),
            channel_width=q(cfg["channel_width_m"], "m"), channel_depth=q(cfg["channel_depth_m"], "m"), rib_width=q(cfg["rib_width_m"], "m"), channel_count=cfg["channel_count"],
            wall_thickness=q(cfg["wall_thickness_m"], "m"), wall_conductivity=q(cfg["wall_conductivity_w_m_k"], "W/m/K"),
            min_temperature=q(feed["min_temperature"], "K"), max_temperature=q(feed["max_temperature"], "K"), max_wall_temperature=q(cfg["max_wall_temperature_k"], "K"),
            max_vapour_pressure=q(feed["vapour_pressure"], "Pa"), direction="exit_to_throat",
        ))
        ordered = tuple(reversed(cooling.segments))
        new_heat = [s.heat_w for s in ordered]
        new_wall = [ordered[0].peak_hot_wall_temperature_k, *[(a.peak_hot_wall_temperature_k + b.peak_hot_wall_temperature_k) / 2 for a, b in pairwise(ordered)], ordered[-1].peak_hot_wall_temperature_k]
        heat_error = math.fsum(abs(a - b) for a, b in zip(new_heat, heat, strict=True))
        wall_error = max(abs(a - b) for a, b in zip(new_wall, wall, strict=True))
        history.append({"iteration": iteration, "heat_l1_residual_w": heat_error, "wall_infinity_residual_k": wall_error, "chamber_temperature_k": gas.temperature_k, "heat_extracted_w": math.fsum(heat), "coolant_heat_pickup_w": cooling.total_heat_w})
        if heat_error <= policy["heat_tolerance"] and wall_error <= policy["wall_temperature_tolerance"]:
            return {"gas": gas, "nozzle": nozzle, "cooling": cooling, "heat_extraction_w": heat, "thermal_history": history, "heat_coupling_residual_w": math.fsum(heat) - cooling.total_heat_w}
        alpha = policy["relaxation"]
        heat = [(1 - alpha) * a + alpha * b for a, b in zip(heat, new_heat, strict=True)]
        wall = [(1 - alpha) * a + alpha * b for a, b in zip(wall, new_wall, strict=True)]
    raise ThermalNotConverged(history)


def assess(design: PropulsionDesign, specification: dict[str, Any]) -> CalculationResult:
    values = validate(specification)
    original = design.to_canonical_json()
    snapshot = PropulsionDesign.from_canonical_dict(json.loads(original))
    if snapshot.cycle_configuration.cycle_type.value != values["cycle_type"] or snapshot.requirements.cycle_type != values["cycle_type"]:
        raise InvalidInputError("Select the same approved cycle in baseline and solver.")
    contour = snapshot.workflow.current_result("nozzle")
    if contour is None or snapshot.workflow.graph.get("nozzle").status is not ResultStatus.CURRENT:
        raise InsufficientDataError("Require an actual CURRENT saved nozzle contour; no invented geometry.")
    rows = contour.outputs["stations"]
    if not 2 <= len(rows) <= 257 or any(b["x_m"] <= a["x_m"] or b["radius_m"] <= a["radius_m"] for a, b in pairwise(rows)):
        raise OutOfRangeError("Require2-257 strictly divergent saved contour stations.")
    ambient_q = snapshot.operating_point.ambient_pressure
    if ambient_q is None or ambient_q.to_si() < 0:
        raise InsufficientDataError("Explicit nonnegative saved ambient pressure required.")
    ambient = ambient_q.to_si()
    cfg = deepcopy(snapshot.subsystem_inputs.get("cooling", {}))
    if values["cooling"]["mode"] == "FUEL_CORE_SERIES" and (not cfg or cfg.get("film_mode") != "none" or cfg.get("direction") != "exit_to_throat"):
        raise OutOfRangeError("Require saved counterflow no-film channel geometry; no silent rerouting or film mass injection.")
    if snapshot.propellant_configuration.fuel_id is None or snapshot.propellant_configuration.oxidizer_id is None:
        raise InsufficientDataError("Explicit saved fuel/oxidizer identities required.")
    chamber = NasaHPChamber(
        snapshot.propellant_configuration.fuel_id, snapshot.propellant_configuration.oxidizer_id,
        values["fuel"]["reference_temperature"], values["oxidizer"]["reference_temperature"],
    )
    keys = list(values["unknowns"])
    units = {**CORE_UNKNOWNS, **GG_UNKNOWNS}
    scales = np.array([values["unknowns"][key]["scale"] for key in keys])
    initial, lower, upper = (np.array([values["unknowns"][key][field] for key in keys]) / scales for field in ("initial", "lower", "upper"))
    tolerance = values["tolerances"]
    last_error = ""
    failure_diagnostics: list[dict[str, Any]] = []

    def evaluate(state: np.ndarray) -> dict[str, Any]:
        unknown = {key: float(value) for key, value in zip(keys, state * scales, strict=True)}
        pc, ox, fuel = (unknown[key] for key in ("chamber_pressure", "oxidizer_flow", "fuel_flow"))
        streams = {}
        for name, mass in (("oxidizer", ox), ("fuel", fuel)):
            feed = values[name]
            gg_flow = unknown["gg_" + name + "_flow"] if "gg" in values else 0.
            flow = mass + gg_flow
            pressure, temperature = feed["tank_pressure"], feed["temperature"]
            work, power = 0., 0.
            if "gg" in values:
                pump, speed = feed["pump"], unknown["shaft_speed"]
                if not pump["speed_min"] <= speed <= pump["speed_max"] or not pump["flow_min"] <= flow <= pump["flow_max"]:
                    raise OutOfRangeError("Pump flow/speed outside declared characteristic window; no extrapolation.")
                result = pump_state(pressure=q(pressure, "Pa"), density=q(feed["density"], "kg/m3"), cp=q(feed["cp"], "J/kg/K"), flow=q(flow, "kg/s"), speed=q(speed, "rad/s"), speed_coefficient=q(pump["speed_coefficient"], "Pa*s2/rad2"), flow_coefficient=q(pump["flow_coefficient"], "Pa*s2/kg2"), efficiency=pump["efficiency"])
                pressure, work, power = result.discharge_pressure_pa, result.specific_work_j_kg, result.power_w
                temperature += result.temperature_rise_k
            if not feed["min_temperature"] <= temperature <= feed["max_temperature"] or pressure <= feed["vapour_pressure"]:
                raise OutOfRangeError("Pump discharge outside declared single-phase liquid window.")
            delta_h = liquid_enthalpy_increment(temperature=q(feed["temperature"], "K"), reference_temperature=q(feed["reference_temperature"], "K"), pressure=q(feed["tank_pressure"], "Pa"), reference_pressure=q(feed["reference_pressure"], "Pa"), density=q(feed["density"], "kg/m3"), cp=q(feed["cp"], "J/kg/K")) + work
            streams[name] = {"core_flow_kg_s": mass, "gg_flow_kg_s": gg_flow, "pump_flow_kg_s": flow, "discharge_pressure_pa": pressure, "coolant_inlet_temperature_k": temperature, "specific_enthalpy_increment_j_kg": delta_h, "pump_specific_work_j_kg": work, "pump_power_w": power}
        base_h = sum(streams[name]["core_flow_kg_s"] * streams[name]["specific_enthalpy_increment_j_kg"] for name in streams) / (ox + fuel)
        thermal = _thermal(chamber, pc, ox, fuel, base_h, streams["fuel"]["discharge_pressure_pa"], streams["fuel"]["coolant_inlet_temperature_k"], rows, cfg, values)
        nozzle, gas, cooling = thermal["nozzle"], thermal["gas"], thermal["cooling"]
        if pc <= ambient or nozzle.stations[-1].pressure_pa < ambient:
            raise OutOfRangeError("Only underexpanded/matched supersonic nozzle supported; backpressure/shock/separation not solved.")
        checks = []

        def check(name: str, value: float, unit: str, kind: str):
            limit = tolerance[kind]
            checks.append({"name": name, "value": value, "unit": unit, "tolerance": limit, "passed": abs(value) <= limit})

        for name, stream in streams.items():
            feed = values[name]
            drop = pressure_loss(q(stream["core_flow_kg_s"], "kg/s"), q(feed["core_resistance"], "Pa*s2/kg2"))
            cooling_drop = cooling.total_pressure_loss_pa if cooling and name == "fuel" else 0.
            check(name + "_core_pressure", stream["discharge_pressure_pa"] - pc - drop - cooling_drop, "Pa", "pressure")
            rise = (cooling.total_heat_w / stream["core_flow_kg_s"] if cooling and name == "fuel" else 0.)
            injection_t = stream["coolant_inlet_temperature_k"] + (rise + (stream["discharge_pressure_pa"] - pc) / feed["density"]) / feed["cp"]
            if not feed["min_temperature"] <= injection_t <= feed["max_temperature"] or pc <= feed["vapour_pressure"]:
                raise OutOfRangeError("Core injector liquid state outside declared phase/property window.")
            stream["core_injection_temperature_k"] = injection_t
        check("core_throat_mass", ox + fuel - nozzle.mass_flow_kg_s, "kg/s", "mass_flow")
        nonlinear = [row["value"] / row["tolerance"] for row in checks]
        gg_record = None
        gg_out_energy, gg_cold_energy, shaft_loss, auxiliary = 0., 0., 0., 0.
        if "gg" in values:
            gg = values["gg"]
            pg, go, gf = (unknown[key] for key in ("gg_pressure", "gg_oxidizer_flow", "gg_fuel_flow"))
            gg_mass = go + gf
            delta = sum(streams[name]["gg_flow_kg_s"] * streams[name]["specific_enthalpy_increment_j_kg"] for name in streams) / gg_mass
            gg_gas = _chamber(chamber, pg, go, gf, delta)
            if not values["cooling"]["gas_min_temperature"] <= gg_gas.temperature_k <= values["cooling"]["gas_max_temperature"]:
                raise OutOfRangeError("GG state outside declared frozen-gas property window.")
            gamma = gg_gas.cp_j_kg_k / (gg_gas.cp_j_kg_k - gg_gas.gas_constant_j_kg_k)
            if gg["exhaust_pressure"] / pg > (2 / (gamma + 1))**(gamma / (gamma - 1)):
                raise OutOfRangeError("GG effective throat is not choked under the supplied backpressure.")
            gg_nozzle = _nozzle(pg, gg_gas, [gg["throat_area"], 2 * gg["throat_area"]], [0.])
            work, tout = Turbine(q(gg_gas.temperature_k, "K"), q(pg, "Pa"), q(gg["exhaust_pressure"], "Pa"), q(gg_gas.cp_j_kg_k, "J/kg/K"), gamma, gg["turbine_efficiency"], gg["shaft_efficiency"]).evaluate()
            turbine = gg_mass * work
            demand = sum(streams[name]["pump_power_w"] for name in streams) + gg["auxiliary_power"]
            for name in streams:
                loss = pressure_loss(q(streams[name]["gg_flow_kg_s"], "kg/s"), q(values[name]["gg_resistance"], "Pa*s2/kg2"))
                check(name + "_gg_pressure", streams[name]["discharge_pressure_pa"] - pg - loss, "Pa", "pressure")
                feed = values[name]
                injection_t = streams[name]["coolant_inlet_temperature_k"] + (streams[name]["discharge_pressure_pa"] - pg) / (feed["density"] * feed["cp"])
                if not feed["min_temperature"] <= injection_t <= feed["max_temperature"] or pg <= feed["vapour_pressure"]:
                    raise OutOfRangeError("GG injector liquid state outside declared phase/property window.")
            check("gg_throat_mass", gg_mass - gg_nozzle.mass_flow_kg_s, "kg/s", "mass_flow")
            check("shaft_power", gg["shaft_efficiency"] * turbine - demand, "W", "power")
            nonlinear = [row["value"] / row["tolerance"] for row in checks]
            check("gg_HP_enthalpy", gg_gas.enthalpy_residual_j_kg, "J/kg", "specific_energy")
            check("turbine_energy", gg_mass * gg_gas.cp_j_kg_k * (gg_gas.temperature_k - tout) - turbine, "W", "power")
            gg_record = {"gas": asdict(gg_gas), "turbine_power_w": turbine, "pump_auxiliary_power_w": demand, "turbine_outlet_temperature_k": tout}
            gg_out_energy = gg_mass * (gg_gas.product_enthalpy_j_kg + gg_gas.cp_j_kg_k * (tout - gg_gas.temperature_k))
            gg_cold_energy = gg_mass * gg_gas.reference_enthalpy_j_kg
            shaft_loss = turbine * (1 - gg["shaft_efficiency"])
            auxiliary = gg["auxiliary_power"]
        check("core_HP_enthalpy", gas.enthalpy_residual_j_kg, "J/kg", "specific_energy")
        check("nozzle_energy", nozzle.energy_residual_w, "W", "power")
        check("nozzle_momentum_max", max(abs(v) for v in nozzle.momentum_residuals_n), "N", "momentum")
        check("heat_exchange_coupling", thermal["heat_coupling_residual_w"], "W", "power")
        if cooling:
            check("coolant_energy", cooling.energy_residual_w, "W", "power")
        # Independent product enthalpy and computed exit total state, relative
        # to common database reactant enthalpy; internal regeneration cancels.
        core_net = (ox + fuel) * (gas.product_enthalpy_j_kg + nozzle.stations[-1].total_enthalpy_j_kg - gas.cp_j_kg_k * gas.temperature_k - gas.reference_enthalpy_j_kg - base_h)
        check("core_net_energy_including_regeneration", core_net, "W", "power")
        core_out_energy = (ox + fuel) * (gas.product_enthalpy_j_kg + nozzle.stations[-1].total_enthalpy_j_kg - gas.cp_j_kg_k * gas.temperature_k)
        cold_energy = (ox + fuel) * gas.reference_enthalpy_j_kg + gg_cold_energy + sum(s["pump_flow_kg_s"] * (s["specific_enthalpy_increment_j_kg"] - s["pump_specific_work_j_kg"]) for s in streams.values())
        external_energy = core_out_energy + gg_out_energy + shaft_loss + auxiliary - cold_energy
        check("external_engine_energy", external_energy, "W", "power")
        thrust = nozzle.mass_flow_kg_s * nozzle.stations[-1].velocity_m_s + (nozzle.stations[-1].pressure_pa - ambient) * nozzle.stations[-1].area_m2
        return {"unknowns": {name: {"value": float(value), "unit": units[name]} for name, value in unknown.items()}, "nonlinear": nonlinear, "residuals": checks, "core": {"thrust_n": thrust, "mass_flow_kg_s": ox + fuel, "mixture_ratio": ox / fuel, "gas": asdict(gas), "nozzle": asdict(nozzle)}, "streams": streams, "gas_generator": gg_record, "cooling": asdict(cooling) if cooling else None, "thermal_history": thermal["thermal_history"], "heat_extraction_w": thermal["heat_extraction_w"], "external_energy_ledger_w": {"cold_feed_common_reference": cold_energy, "core_exit_total_enthalpy": core_out_energy, "gg_exit_total_enthalpy": gg_out_energy, "shaft_loss_to_environment": shaft_loss, "auxiliary_boundary": auxiliary, "signed_residual": external_energy}}

    def residual(state):
        nonlocal last_error, failure_diagnostics
        try:
            return np.array(evaluate(state)["nonlinear"])
        except CosmosError as error:
            last_error = type(error).__name__ + ": " + str(error)
            failure_diagnostics = error.history if isinstance(error, ThermalNotConverged) else []
            raise ValueError(last_error) from error

    policy = values["solver"]
    solved = solve(residual, initial, lower, upper, step=policy["difference_step"], tolerance=policy["residual_tolerance"], max_iterations=policy["max_iterations"], max_evaluations=policy["max_evaluations"], max_seconds=policy["max_seconds"])
    output = evaluate(np.array(solved.value)) if solved.converged else None
    admissible = output is not None and all(row["passed"] for row in output["residuals"])
    return CalculationResult(
        calculation_type="cycle.engine_operating_point", status=ResultStatus.CURRENT if admissible else ResultStatus.FAILED,
        model_id=HEATED_NOZZLE.model_id, model_version="1",
        inputs={"baseline_canonical_text": original, "specification": deepcopy(specification), "contour_result_id": contour.result_id},
        outputs={"workflow_cycle_complete": False, "solved_candidate_usable": admissible, "execution_status": "COMPLETED", "termination_reason": solved.termination, "numerical_convergence": solved.converged, "conservation_checks": "PASS" if admissible else "NOT_PASSED", "physical_admissibility": "PASS_DECLARED_ENVELOPE" if admissible else "NO_ACCEPTED_STATE", "solution_verification": "INDEPENDENT_SOFTWARE_FIXTURES_NOT_PHYSICAL_VALIDATION", "experimental_validation": "NOT_PERFORMED", "solver": asdict(solved), "last_rejected_trial": last_error or None, "last_failed_thermal_history": failure_diagnostics, "candidate": output if admissible else None, "unaccepted_diagnostics": output if not admissible else None, "residuals": output["residuals"] if output else [], "scope": "Selected steady PF/GG network and two-way HP/regenerative/frozen nonadiabatic divergent nozzle; regulated tanks, no film injection/shock/phase-change/transient model", "physical_validation": "NOT_PERFORMED"},
        assumptions=HEATED_NOZZLE.assumptions,
        warnings=HEATED_NOZZLE.limitations + ("No experimental measurements or engineering/hardware acceptance. Candidate does not mutate the upstream workflow.",),
        verification=VerificationInfo(status="SOFTWARE_VERIFIED_DECLARED_MODEL"), validation=ValidationInfo(status="NOT_PERFORMED"),
        validity=ValidityInfo(status=ValidityState.VALID if admissible else ValidityState.UNKNOWN, checks=("Explicit property/map windows, branch pressures, choking, mass/energy/momentum/power and thermal consistency",) if admissible else (), valid_range="Declared selected single-phase PF/GG/frozen divergent model only"),
        provenance=ProvenanceInfo(source=HEATED_NOZZLE.source, model="Selected engine operating-point with NASA HP feedback", version="1"),
    )
