"""Authenticated managed pressure-fed routes and lossless source/CSV export."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from typing import Any

from api.geometry_projects import BinarySource
from api.pressure_fed import _methods as model_methods
from systems.projects.authority import InvalidRecord, Principal, RecordNotFound
from systems.projects.pressure_fed import ManagedPressureFed


def methods() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    return {
        **model_methods(),
        **{
            name: sha256((root / name).read_bytes()).hexdigest()
            for name in (
                "api/pressure_fed_projects.py",
                "systems/projects/pressure_fed.py",
            )
        },
    }


class PressureFedAPI:
    filename_prefix = "pressure-fed"

    def __init__(self, service: ManagedPressureFed) -> None:
        self.service = service

    def csv(self, value: dict[str, Any]) -> bytes:
        return residual_csv(value)

    def handle(
        self,
        actor: Principal,
        method: str,
        project: str,
        parts: list[str],
        query: dict[str, list[str]],
        body: dict[str, Any],
    ) -> dict[str, Any] | BinarySource:
        from api.project_authority import expected_head

        repo = self.service.repository
        list_route = parts in ([], ["captures"]) and method == "GET"
        allowed = (
            {"limit", "after"}
            if list_route
            else {"commit"}
            if method == "GET"
            and parts
            and parts[0] not in {"capabilities", "captures"}
            else set()
        )
        if set(query) - allowed:
            raise InvalidRecord(
                "Unsupported assessment query; exact source context must not be ignored."
            )
        if parts == ["capabilities"] and method == "GET":
            return {
                "ok": True,
                "schema": "cosmos.pressure-fed-assessment-input.v1",
                "scope": "Assumed-state, specified-flow, steady incompressible core-only pressure budget. No full cycle closure, CEA/diversion coupling or pressurant sizing.",
                "regime": "STEADY_SINGLE_PHASE_INCOMPRESSIBLE",
                "pressurant_boundary": "REGULATED_TANK_PRESSURE",
                "flow_accounting": "CORE_ONLY_NO_DIVERSION",
                "losses": ["feed_line", "valves", "cooling"],
                "station_convention": "Tank free surface (zero liquid surface velocity) to injector inlet manifold. Injector static delta-p defines sink pressure; other loss entries are irreversible upstream losses at the declared core flow/temperature.",
                "execution": "Bounded synchronous evaluation outside SQL; input capture precedes evaluation. No background job/cancellation claim.",
            }
        if list_route:
            capture = parts == ["captures"]
            objects = repo.list_objects(
                actor,
                project,
                domain=self.service.inputs_domain if capture else self.service.domain,
                limit=int(query.get("limit", ["20"])[0]),
                after_id=query.get("after", [""])[0],
            )
            return {
                "ok": True,
                "captures" if capture else "assessments": [
                    asdict(item) for item in objects
                ],
            }
        if not parts and method == "POST":
            if set(body) != {
                "baseline_commit_id",
                "expected_baseline",
                "specification",
                "operation_id",
            }:
                raise InvalidRecord(
                    "Supply only an exact baseline/head, explicit specification and operation ID."
                )
            command_hash = sha256(
                json.dumps(
                    {"project": project, "body": body},
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode()
            ).hexdigest()
            source = self.service.create(
                actor,
                project,
                body["baseline_commit_id"],
                expected_head(body["expected_baseline"]),
                body["specification"],
                body["operation_id"],
                command_hash,
            )
            return self.service.read(actor, source)
        if len(parts) == 2 and parts[0] == "captures" and method == "GET":
            source = repo.get_snapshot(
                actor, project, domain=self.service.inputs_domain, object_id=parts[1]
            )
            return self.service.read_input(actor, source)
        if (
            len(parts) in {1, 2}
            and method == "GET"
            and parts[0] not in {"capabilities", "captures"}
        ):
            source = (
                repo.resolve_snapshot(actor, project, query["commit"][0])
                if "commit" in query
                else repo.get_snapshot(
                    actor, project, domain=self.service.domain, object_id=parts[0]
                )
            )
            if source.domain != self.service.domain or source.object_id != parts[0]:
                raise RecordNotFound(
                    "Exact pressure-fed assessment identity does not match."
                )
            value = self.service.read(actor, source)
            if len(parts) == 1:
                return value
            if parts[1] == "record.json":
                return BinarySource(
                    self.filename_prefix + "-record.json",
                    source.payload,
                    source.head.content_hash,
                )
            if parts[1] == "inputs.json":
                inputs = repo.resolve_snapshot(
                    actor, project, value["record"]["capture_commit_id"]
                )
                return BinarySource(
                    self.filename_prefix + "-inputs.json",
                    inputs.payload,
                    inputs.head.content_hash,
                )
            if parts[1] == "residuals.csv":
                if value["record"]["status"] != "COMPLETED":
                    raise InvalidRecord(
                        "A failed assessment has no calculated residual rows. Inspect the failure/input originals."
                    )
                raw = self.csv(value)
                return BinarySource(
                    self.filename_prefix + "-residuals.csv",
                    raw,
                    sha256(raw).hexdigest(),
                )
        raise RecordNotFound("Pressure-fed assessment route not found.")


def residual_csv(value: dict[str, Any]) -> bytes:
    record, authority = value["record"], value["authority"]
    output = io.StringIO(newline="")
    numeric = (
        "mass_flow_kg_s",
        "tank_mass_flow_kg_s",
        "volumetric_flow_m3_s",
        "outlet_velocity_m_s",
        "kinetic_pressure_change_pa",
        "elevation_pressure_change_pa",
        "irreversible_loss_pa",
        "required_source_pressure_pa",
        "supplied_source_pressure_pa",
        "required_sink_pressure_pa",
        "pressure_residual_pa",
        "mass_residual_kg_s",
        "dissipated_mechanical_power_w",
    )
    fields = [
        "stream",
        *numeric,
        "pressure_state",
        "mass_matches_core_demand",
        "project_id",
        "commit_id",
        "content_sha256",
        "baseline_commit_id",
        "capture_commit_id",
        "upstream_current",
        "physical_validation",
    ]
    writer = csv.DictWriter(output, fields)
    writer.writeheader()
    for name, row in record["evaluation"]["result"]["outputs"]["streams"].items():
        writer.writerow(
            {
                "stream": name,
                **{key: row[key] for key in numeric},
                "pressure_state": row["pressure_state"],
                "mass_matches_core_demand": row["mass_matches_core_demand"],
                "project_id": authority["project_id"],
                "commit_id": authority["commit_id"],
                "content_sha256": authority["head"]["content_hash"],
                "baseline_commit_id": record["baseline_commit_id"],
                "capture_commit_id": record["capture_commit_id"],
                "upstream_current": value["upstream_current"],
                "physical_validation": "NOT_PERFORMED",
            }
        )
    return output.getvalue().encode()
