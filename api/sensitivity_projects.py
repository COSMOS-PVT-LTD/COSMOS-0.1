"""Authenticated sensitivity composition; delegates unchanged scientific work."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from api.propulsion_workflow import run_phase3, update_requirements
from core.quantity import Quantity
from systems.projects.authority import InvalidRecord, Principal, RecordNotFound
from systems.projects.models import PropulsionDesign
from systems.projects.sensitivity import DOMAIN, OUTPUTS, PARAMETERS, ManagedSensitivity


def methods() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    paths = {
        path
        for directory in (
            "core",
            "physics/compressible_flow",
            "physics/thermochemistry",
            "systems/stages",
            "systems/workflow",
            "systems/contracts",
        )
        for path in (root / directory).rglob("*.py")
    }
    paths.update(
        root / name
        for name in (
            "api/propulsion_workflow.py",
            "api/sensitivity_projects.py",
            "numerics/sensitivity/local.py",
            "numerics/utilities/numerical_checks.py",
            "systems/projects/sensitivity.py",
            "systems/projects/models.py",
        )
    )
    return {
        str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


def evaluate(design: PropulsionDesign, parameter: str, value: float) -> dict[str, Any]:
    original = design.workflow.current_result("performance")
    if original is None:
        raise InvalidRecord("Current performance input snapshot required.")
    inputs = original.inputs
    call = {
        "chamber_temperature_k": Quantity.from_canonical_dict(
            inputs["chamber_temperature"]
        ).to_si(),
        "gamma": inputs["gamma"]["value"],
        "molecular_weight_kg_per_mol": Quantity.from_canonical_dict(
            inputs["molar_mass"]
        ).to_si(),
        "throat_area_m2": inputs["throat_area_m2"]["value"],
        "expansion_ratio": inputs["expansion_ratio"]["value"],
    }
    if parameter in {"chamber_pressure_pa", "ambient_pressure_pa"}:
        update_requirements(
            design,
            {
                {
                    "chamber_pressure_pa": "target_chamber_pressure",
                    "ambient_pressure_pa": "ambient_pressure",
                }[parameter]: value
            },
        )
    else:
        call[parameter] = value
    captured = {
        "requirements": design.requirements.to_canonical_dict(),
        "propellants": design.propellant_configuration.to_canonical_dict(),
        "cycle": design.cycle_configuration.to_canonical_dict(),
        "thermochemistry_configuration": design.thermochemistry_configuration,
        "call": call,
    }
    run_phase3(design, **call)
    performance = design.workflow.results["performance"].to_canonical_dict()
    thermo = design.workflow.results["thermochemistry"].to_canonical_dict()

    def wire(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)

    return {
        "input_canonical_json": wire(captured),
        "performance": performance,
        "performance_canonical_json": wire(performance),
        "thermochemistry_canonical_json": wire(thermo),
    }


class SensitivityAPI:
    def __init__(self, service: ManagedSensitivity) -> None:
        self.service = service

    def handle(
        self,
        actor: Principal,
        method: str,
        project: str,
        parts: list[str],
        query: dict[str, list[str]],
        body: dict[str, Any],
    ) -> dict[str, Any]:
        from api.project_authority import _allowed, expected_head

        repo = self.service.repository
        if set(query) - (
            {"limit", "after"} if not parts and method == "GET" else set()
        ):
            raise InvalidRecord(
                "Unsupported sensitivity query; exact source identity must not be silently ignored."
            )
        if parts == ["capabilities"] and method == "GET":
            return {
                "ok": True,
                "parameters": PARAMETERS,
                "outputs": OUTPUTS,
                "sample_limit": 21,
                "scope": "Explicit assumed-state performance only; CEA/global/cycle sensitivity unsupported in this first slice.",
            }
        if not parts:
            if method == "GET":
                from dataclasses import asdict

                return {
                    "ok": True,
                    "studies": [
                        asdict(item)
                        for item in repo.list_objects(
                            actor,
                            project,
                            domain=DOMAIN,
                            limit=int(query.get("limit", ["20"])[0]),
                            after_id=query.get("after", [""])[0],
                        )
                    ],
                }
            if method == "POST":
                if set(body) != {
                    "baseline_commit_id",
                    "expected_baseline",
                    "specification",
                    "operation_id",
                }:
                    raise InvalidRecord(
                        "An exact baseline/head, specification and operation ID are required; additional fields are refused."
                    )
                _allowed(
                    body,
                    {
                        "baseline_commit_id",
                        "expected_baseline",
                        "specification",
                        "operation_id",
                    },
                )
                command_hash = sha256(
                    json.dumps(
                        {"project": project, "body": body},
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    ).encode()
                ).hexdigest()
                saved = self.service.create(
                    actor,
                    project,
                    body["baseline_commit_id"],
                    expected_head(body["expected_baseline"]),
                    body["specification"],
                    body["operation_id"],
                    command_hash,
                )
                return self.service.read(actor, saved)
        if len(parts) in {1, 2} and method == "GET":
            saved = repo.get_snapshot(actor, project, domain=DOMAIN, object_id=parts[0])
            value = self.service.read(actor, saved)
            if len(parts) == 1:
                return value
            if parts[1] == "plots":
                from systems.visualization.plots import _plot

                if not value["upstream_current"]:
                    raise InvalidRecord(
                        "Historical/stale sensitivity is inspectable as exact source, not promoted to current curves."
                    )
                record = value["record"]
                specification = record["specification"]
                chunks: list[list[dict[str, Any]]] = [[]]
                unavailable = []
                for index, row in enumerate(record["samples"]):
                    if row["status"] == "EVALUATED":
                        chunks[-1].append(
                            {
                                "parameter_value": row["value"],
                                "output_value": row["output"],
                            }
                        )
                    else:
                        unavailable.append(
                            {
                                "index": index,
                                "value": row["value"],
                                "status": row["status"],
                                "reason": row["error"],
                            }
                        )
                        chunks.append([])
                source = {
                    "domain": DOMAIN,
                    "project_id": project,
                    "commit_id": saved.commit_id,
                    "content_sha256": saved.head.content_hash,
                    "baseline_commit_id": record["baseline_commit_id"],
                    "freshness": "current",
                    "status": record["status"],
                    "method_id": record["method"],
                    "model_id": record["method"],
                    "method_sources": record["method_sources"],
                    "source_canonical_json": saved.payload.decode(),
                    "assumptions": record["limitations"],
                    "warnings": [
                        "Invalid samples are never interpolated; numerical sensitivity is not physical validation."
                    ],
                    "verification": "Numerical method software tests; not physical validation",
                    "validation": "NOT_PERFORMED",
                }
                plots = [
                    _plot(
                        "sensitivity-" + str(index),
                        OUTPUTS[specification["output"]][0],
                        rows,
                        (
                            "parameter_value",
                            PARAMETERS[specification["parameter"]][0],
                            specification["unit"],
                        ),
                        [("output_value", "Computed response")],
                        record["output_unit"],
                        source,
                        record["limitations"],
                    )
                    for index, rows in enumerate(chunks)
                    if len(rows) >= 2
                ]
                for index, rows in enumerate(chunks):
                    if len(rows) == 1:
                        unavailable.append(
                            {
                                "segment": index,
                                "reason": "Isolated valid sample retained in source; not connected across an invalid gap.",
                            }
                        )
                return {
                    "schema_version": "cosmos-plots-v1",
                    "plots": plots,
                    "unavailable": unavailable,
                    "production_handoff": False,
                }
        raise RecordNotFound("Sensitivity route not found.")
