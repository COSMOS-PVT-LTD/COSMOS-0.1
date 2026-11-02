"""Immutable propulsion evidence preparation on the existing project authority."""

from __future__ import annotations

import base64
import csv
import json
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from core.quantity import Quantity
from systems.contracts.results import ResultStatus
from systems.persistence.project_repository import Dependency, ProjectRepository
from systems.projects.authority import (
    Head,
    HeadConflict,
    InvalidRecord,
    Principal,
    RecordNotFound,
    SavedSnapshot,
    StoreUnavailable,
    require_active_project,
)
from systems.projects.pressure_fed import payload
from systems.projects.propulsion_authority import (
    PropulsionProjectService,
    decode_design,
)
from validation import propulsion as vv

PLAN = "propulsion-validation-plan"
DATA = "propulsion-measurement"
ASSESSMENT = "propulsion-validation-assessment"
TARGETS = {
    "thrust": ("performance", "thrust", "N"),
    "core_mass_flow": ("performance", "mass_flow", "kg/s"),
    "core_specific_impulse": ("performance", "specific_impulse", "s"),
    "coolant_outlet_temperature": ("cooling", "outlet_temperature_k", "K"),
    "coolant_pressure_loss": ("cooling", "total_pressure_loss_pa", "Pa"),
    "coolant_heat_pickup": ("cooling", "total_heat_w", "W"),
    "nozzle_peak_hot_wall_temperature": ("cooling", "max_hot_wall_temperature_k", "K"),
}


def candidate(source: SavedSnapshot, target_names: list[str]) -> dict[str, Any]:
    if source.domain == "engine-operating-point":
        from systems.projects.operating_validation import (
            candidate as operating_candidate,
        )
        return operating_candidate(source, target_names)
    if (
        type(target_names) is not list
        or not 1 <= len(target_names) <= 8
        or any(type(name) is not str or name not in TARGETS for name in target_names)
        or len(set(target_names)) != len(target_names)
    ):
        raise InvalidRecord(
            "Choose1-8 unique supported prediction targets; imposed chamber pressure is not a validation prediction."
        )
    design = decode_design(source)
    captured = {}

    def current(stage):
        result = design.workflow.current_result(stage)
        if (
            result is None
            or design.workflow.graph.get(stage).status is not ResultStatus.CURRENT
        ):
            raise InvalidRecord(
                "CURRENT retained "
                + stage
                + " source required before planning validation."
            )
        captured[stage] = result.to_canonical_dict()
        if result.validity.status.value == "OUT_OF_RANGE":
            raise InvalidRecord(
                "Out-of-range candidate cannot enter a validation plan."
            )
        return result

    op, props, thermo, perf = (
        current(stage)
        for stage in (
            "operating_point",
            "propellants",
            "thermochemistry",
            "performance",
        )
    )
    if (thermo.inputs.get("engine") == "nasa/cea") != (
        perf.calculation_type == "performance.cea_ideal_nozzle"
    ):
        raise InvalidRecord(
            "CEA/performance source mismatch; no assumed-state validation fallback."
        )
    if (
        thermo.inputs.get("engine") == "nasa/cea"
        and perf.inputs.get("thermochemistry_result_id") != thermo.result_id
    ):
        raise InvalidRecord(
            "CEA prediction references a different thermochemistry result."
        )
    conditions: dict[str, Any] = {}
    properties: dict[str, Any] = {}

    def row(mapping, name, value, unit, source_text):
        if type(value) is not str:
            value = vv.number(value, name)
        mapping[name] = {"value": value, "unit": unit, "source": source_text}

    for name, key in (
        ("chamber_pressure", "chamber_pressure"),
        ("ambient_pressure", "ambient_pressure"),
    ):
        pressure = Quantity.from_canonical_dict(perf.inputs[key])
        if pressure.unit.symbol != "Pa":
            raise InvalidRecord(
                "Retained performance pressure must have explicit SI units."
            )
        row(conditions, name, pressure.to_si(), "Pa", perf.result_id)
    row(
        conditions, "core_mixture_ratio", op.outputs["mixture_ratio"], "1", op.result_id
    )
    for name in ("oxidizer", "fuel"):
        selected = getattr(design.propellant_configuration, name + "_id")
        if not selected or props.inputs.get(name + "_id") != selected:
            raise InvalidRecord("Retained propellant identities disagree.")
        row(conditions, name + "_id", selected, "1", props.result_id)
    for name, key, unit in (
        ("throat_area", "throat_area_m2", "m2"),
        ("expansion_ratio", "expansion_ratio", "1"),
    ):
        value = perf.inputs[key]
        if value.get("unit") != unit:
            raise InvalidRecord("Retained nozzle geometry units disagree.")
        row(conditions, name, value["value"], unit, perf.result_id)
    if thermo.inputs.get("engine") == "nasa/cea":
        for name in ("fuel_temperature_k", "oxidizer_temperature_k"):
            row(
                conditions,
                name,
                design.thermochemistry_configuration[name],
                "K",
                thermo.result_id,
            )
    else:
        if perf.calculation_type != "performance.choked_nozzle_thrust":
            raise InvalidRecord(
                "Unsupported core performance model; no validation relabelling."
            )
        row(
            properties,
            "assumed_gamma",
            design.operating_point.gamma,
            "1",
            thermo.result_id,
        )
        row(
            properties,
            "assumed_molar_mass",
            design.operating_point.molecular_weight,
            "kg/mol",
            thermo.result_id,
        )
        if design.operating_point.chamber_temperature is None:
            raise InvalidRecord("Retained assumed chamber temperature is required.")
        row(
            conditions,
            "assumed_chamber_temperature",
            design.operating_point.chamber_temperature.to_si(),
            "K",
            thermo.result_id,
        )
    predictions = {}
    for name in target_names:
        stage, key, unit = TARGETS[name]
        result = current(stage)
        value = result.outputs[key]
        if type(value) is dict:
            if "magnitude" in value:
                measured = Quantity.from_canonical_dict(value)
                if measured.unit.symbol != unit:
                    raise InvalidRecord(
                        "Prediction quantity units differ from target contract."
                    )
                value = measured.to_si()
            else:
                if value.get("unit") != unit:
                    raise InvalidRecord("Prediction units differ from target contract.")
                value = value["value"]
        predictions[name] = {
            "value": vv.number(value, name),
            "unit": unit,
            "stage": stage,
            "source_result_id": result.result_id,
            "model_id": result.model_id,
            "validity": result.validity.to_canonical_dict(),
        }
    if any(TARGETS[name][0] == "cooling" for name in target_names):
        cooling = current("cooling")
        nozzle, thermal = current("nozzle"), current("thermal")
        if (
            cooling.inputs.get("nozzle_result_id") != nozzle.result_id
            or cooling.inputs.get("thermal_result_id") != thermal.result_id
        ):
            raise InvalidRecord(
                "Cooling prediction has a different nozzle/thermal source."
            )
        cfg = cooling.inputs
        for name, unit in {
            "coolant_mass_flow_kg_s": "kg/s",
            "inlet_temperature_k": "K",
            "inlet_pressure_pa": "Pa",
            "channel_width_m": "m",
            "channel_depth_m": "m",
            "channel_count": "1",
            "wall_thickness_m": "m",
        }.items():
            row(conditions, name, cfg[name], unit, cooling.result_id)
        row(
            conditions,
            "geometry_coverage",
            "divergent_nozzle_only",
            "1",
            cooling.result_id,
        )
        for name, unit in {
            "density_kg_m3": "kg/m3",
            "viscosity_pa_s": "Pa*s",
            "conductivity_w_m_k": "W/m/K",
            "cp_j_kg_k": "J/kg/K",
            "wall_conductivity_w_m_k": "W/m/K",
        }.items():
            row(properties, name, cfg[name], unit, cfg["property_source"])
        for name, unit in {
            "viscosity_pa_s": "Pa*s",
            "conductivity_w_m_k": "W/m/K",
            "cp_j_kg_k": "J/kg/K",
            "wall_temperature_k": "K",
        }.items():
            row(
                properties,
                "gas_reference_" + name,
                cfg["gas_properties"][name],
                unit,
                thermal.result_id,
            )
        row(conditions, "film_mode", cfg["film_mode"], "1", cooling.result_id)
        if cfg["film_mode"] == "gaseous_slot":
            for name, unit in {
                "film_slot_x_m": "m",
                "film_slot_height_m": "m",
                "film_blowing_ratio": "1",
                "film_temperature_k": "K",
                "film_cp_j_kg_k": "J/kg/K",
                "film_delta0_m": "m",
                "film_delta_growth_rate": "1",
                "film_valid_length_m": "m",
            }.items():
                row(conditions, name, cfg[name], unit, cfg["film_source"])
    return {
        "baseline_commit_id": source.commit_id,
        "baseline_sha256": source.head.content_hash,
        "baseline_canonical_json": source.payload.decode(),
        "predictions": predictions,
        "conditions": conditions,
        "properties": properties,
        "source_results": captured,
        "scope": "Existing retained core/partial cooling predictions only; not full-engine operating-point or thermal/combustion-feedback validation",
    }


class PropulsionValidation:
    def __init__(
        self, repository: ProjectRepository, methods: Callable[[], dict[str, str]],
        operating_current: Callable[[Principal, SavedSnapshot], bool] | None = None,
    ) -> None:
        self.repository, self.methods = repository, methods
        self.loaded_methods = methods()
        self.operating_current = operating_current

    def candidate(self, actor: Principal, source: SavedSnapshot, targets: list[str]) -> dict[str, Any]:
        if source.domain == "engine-operating-point":
            if self.operating_current is None or not self.operating_current(actor, source):
                raise InvalidRecord("Require a current usable operating candidate with exact current methods/runtime and upstream dependencies.")
        elif source.domain != "propulsion":
            raise RecordNotFound("Unsupported propulsion prediction source domain.")
        return candidate(source, targets)

    def _source(
        self, actor: Principal, project: str, commit: str, domain: str
    ) -> SavedSnapshot:
        source = self.repository.resolve_snapshot(actor, project, commit)
        if source.domain != domain:
            raise RecordNotFound("Exact validation source has a different domain.")
        return source

    def create(
        self,
        actor: Principal,
        project: str,
        kind: str,
        body: dict[str, Any],
        command_hash: str,
    ) -> SavedSnapshot:
        actor.require(write=True)
        repo = self.repository
        require_active_project(repo.get_project(actor, project))
        domain = {"plans": PLAN, "measurements": DATA, "assessments": ASSESSMENT}.get(
            kind
        )
        if domain is None:
            raise InvalidRecord("Unsupported validation command.")
        operation = body.get("operation_id")
        if type(operation) is not str or not operation or len(operation) > 128:
            raise InvalidRecord("Explicit bounded operation ID required.")
        replay = repo.resolve_command(
            actor, project, operation_id=operation, command_hash=command_hash
        )
        if replay is not None:
            if replay.domain != domain:
                raise InvalidRecord(
                    "Operation belongs to a different evidence command."
                )
            return replay
        methods = self.methods()
        if methods != self.loaded_methods:
            raise StoreUnavailable(
                "Validation method sources changed; restart before a new command. Original evidence is unchanged."
            )
        dependencies: tuple[Dependency, ...]
        try:
            if kind == "plans":
                vv.fields(
                    body,
                    {
                        "baseline_commit_id",
                        "expected_baseline",
                        "specification",
                        "operation_id",
                    },
                    "plan command",
                )
                source = repo.resolve_snapshot(actor, project, body["baseline_commit_id"])
                current = repo.get_snapshot(
                    actor, project, domain=source.domain, object_id=source.object_id
                )
                vv.fields(
                    body["expected_baseline"],
                    {"version", "content_hash"},
                    "baseline head",
                )
                if (
                    type(body["expected_baseline"]["version"]) is not int
                    or type(body["expected_baseline"]["content_hash"]) is not str
                ):
                    raise ValueError(
                        "Baseline head version/hash require exact integer/text types, not Boolean."
                    )
                if source.commit_id != current.commit_id or body[
                    "expected_baseline"
                ] != asdict(source.head):
                    raise HeadConflict(current.head)
                value = vv.plan(
                    body["specification"],
                    self.candidate(actor, source, list(body["specification"]["targets"])),
                )
                dependencies = (Dependency("candidate-baseline", source.commit_id),)
            elif kind == "measurements":
                vv.fields(
                    body,
                    {"plan_commit_id", "csv_base64", "provenance", "operation_id"},
                    "measurement command",
                )
                source = self._source(actor, project, body["plan_commit_id"], PLAN)
                original = json.loads(source.payload)
                encoded = body["csv_base64"]
                if (
                    type(encoded) is not str
                    or len(encoded) > 4 * vv.MAX_CSV_BYTES // 3 + 8
                ):
                    raise ValueError("Bounded base64 CSV originals required.")
                raw = base64.b64decode(encoded, validate=True)
                value = vv.measurement(raw, body["provenance"], original)
                value.update(
                    {"plan_commit_id": source.commit_id, "csv_base64": encoded}
                )
                dependencies = (Dependency("predeclared-plan", source.commit_id),)
            else:
                vv.fields(
                    body,
                    {"plan_commit_id", "measurement_commit_id", "operation_id"},
                    "assessment command",
                )
                source = self._source(actor, project, body["plan_commit_id"], PLAN)
                data_source = self._source(
                    actor, project, body["measurement_commit_id"], DATA
                )
                data = json.loads(data_source.payload)
                if data["plan_commit_id"] != source.commit_id:
                    raise ValueError(
                        "Measurements belong to a different exact predeclared plan."
                    )
                value = vv.compare(json.loads(source.payload), data)
                value.update(
                    {
                        "plan_commit_id": source.commit_id,
                        "measurement_commit_id": data_source.commit_id,
                    }
                )
                dependencies = (
                    Dependency("predeclared-plan", source.commit_id),
                    Dependency("measurement-original", data_source.commit_id),
                )
        except (ValueError, TypeError, KeyError, OverflowError, csv.Error) as error:
            raise InvalidRecord(str(error)) from error
        if self.methods() != methods:
            raise StoreUnavailable(
                "Validation methods changed during command; no new record published."
            )
        value["method_sources"] = methods
        return repo.save_snapshot(
            actor,
            project,
            domain=domain,
            object_id=PropulsionProjectService.new_id(
                actor, project, operation, domain
            ),
            input_revision=source.input_revision,
            payload=payload(value, value["schema"]),
            expected=Head.absent(),
            operation_id=operation,
            command_hash=command_hash,
            dependencies=dependencies,
        )

    def read(self, actor: Principal, source: SavedSnapshot) -> dict[str, Any]:
        if source.domain not in {PLAN, DATA, ASSESSMENT}:
            raise InvalidRecord("Not a supported propulsion evidence source.")
        value = json.loads(source.payload)
        current = self.repository.dependencies_current(
            actor, source.project_id, source.commit_id
        )
        methods_current = (
            value["method_sources"] == self.loaded_methods == self.methods()
        )
        if source.domain != PLAN:
            plan_source = self._source(
                actor, source.project_id, value["plan_commit_id"], PLAN
            )
            current = current and self.read(actor, plan_source)["upstream_current"]
        return {
            "ok": True,
            "authority": {
                "project_id": source.project_id,
                "object_id": source.object_id,
                "domain": source.domain,
                "commit_id": source.commit_id,
                "head": asdict(source.head),
            },
            "record": value,
            "source_canonical_json": source.payload.decode(),
            "upstream_current": current and methods_current,
            "methods_current": methods_current,
            "physical_validation": "NOT_PERFORMED",
            "independent_acceptance": False,
            "scope": "Evidence workflow only; authentic measurements and qualified acceptance cannot be inferred from stored data or passing software comparisons",
        }
