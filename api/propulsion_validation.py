"""Authenticated validation preparation, raw evidence and comparison; no approval route."""

from __future__ import annotations

import base64
import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from typing import Any

from api.engine_operating import methods as operating_methods
from api.geometry_projects import BinarySource
from api.pressure_fed import _methods
from systems.projects.authority import InvalidRecord, Principal, RecordNotFound
from systems.projects.operating_validation import TARGETS as OPERATING_TARGETS
from systems.projects.propulsion_validation import (
    ASSESSMENT,
    DATA,
    PLAN,
    TARGETS,
    PropulsionValidation,
)
from validation import propulsion as vv


class PropulsionEvidenceSource(BinarySource):
    """Download purpose is unreviewed evidence, not a synthetic fixture or acceptance."""


def methods() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    return {
        **_methods(),
        **operating_methods(),
        **{
            name: sha256((root / name).read_bytes()).hexdigest()
            for name in (
                "validation/propulsion.py",
                "systems/projects/propulsion_validation.py",
                "systems/projects/operating_validation.py",
                "api/propulsion_validation.py",
                "systems/stages/subsystems.py",
                "systems/stages/performance.py",
            )
        },
    }


class PropulsionValidationAPI:
    def __init__(self, service: PropulsionValidation) -> None:
        self.service = service

    def handle(
        self,
        actor: Principal,
        method: str,
        project: str,
        parts: list[str],
        query: dict[str, list[str]],
        body: dict[str, Any],
    ) -> Any:
        repo = self.service.repository
        if parts == ["preview"] and method == "GET":
            if set(query) != {"baseline", "targets"}:
                raise InvalidRecord(
                    "Preview requires exact baseline commit and comma-separated target names only."
                )
            source = repo.resolve_snapshot(actor, project, query["baseline"][0])
            return {
                "ok": True,
                "candidate": self.service.candidate(actor, source, query["targets"][0].split(",")),
                "expected_baseline": asdict(source.head),
                "schema": vv.PLAN_SCHEMA,
                "scope": "Read-only predictions/context preview; not measurements or a saved plan",
            }
        if query and not (
            method == "GET"
            and len(parts) == 1
            and parts[0] in {"plans", "measurements", "assessments"}
            and not set(query) - {"limit", "after"}
        ):
            raise InvalidRecord(
                "Unknown evidence query; exact source context must not be ignored."
            )
        if parts == ["capabilities"] and method == "GET":
            return {
                "ok": True,
                "targets": {
                    name: {"stage": stage, "unit": unit}
                    for name, (stage, _key, unit) in TARGETS.items()
                },
                "operating_targets": {name: {"stage": "engine-operating-point", "unit": unit} for name, (_path, unit) in OPERATING_TARGETS.items()},
                "plan_schema": vv.PLAN_SCHEMA,
                "csv_header": vv.CSV_HEADER,
                "max_csv_bytes": vv.MAX_CSV_BYTES,
                "provenance_fields": sorted(vv.PROVENANCE),
                "physical_validation": "NOT_PERFORMED",
                "acceptance_route": "UNSUPPORTED_REQUIRES_INDEPENDENT_QUALIFIED_PROCESS",
            }
        if len(parts) == 1 and parts[0] in {"plans", "measurements", "assessments"}:
            kind = parts[0]
            if method == "POST":
                command_hash = sha256(
                    json.dumps(
                        {"project": project, "kind": kind, "body": body},
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    ).encode()
                ).hexdigest()
                return self.service.read(
                    actor, self.service.create(actor, project, kind, body, command_hash)
                )
            if method == "GET":
                domain = {
                    "plans": PLAN,
                    "measurements": DATA,
                    "assessments": ASSESSMENT,
                }[kind]
                return {
                    "ok": True,
                    "records": [
                        asdict(item)
                        for item in repo.list_objects(
                            actor,
                            project,
                            domain=domain,
                            limit=int(query.get("limit", ["20"])[0]),
                            after_id=query.get("after", [""])[0],
                        )
                    ],
                }
        if len(parts) in {2, 3} and parts[0] == "records" and method == "GET":
            source = repo.resolve_snapshot(actor, project, parts[1])
            value = self.service.read(actor, source)
            if len(parts) == 2:
                return value
            if parts[2] == "record.json":
                return PropulsionEvidenceSource(
                    "propulsion-validation-record.json",
                    source.payload,
                    source.head.content_hash,
                )
            raw = None
            if parts[2] == "measurement-template.csv" and source.domain == PLAN:
                raw = vv.template(value["record"])
            elif parts[2] == "measurement-original.csv" and source.domain == DATA:
                raw = base64.b64decode(value["record"]["csv_base64"], validate=True)
            elif parts[2] == "metadata-template.json" and source.domain == PLAN:
                raw = json.dumps(
                    {key: "" for key in sorted(vv.PROVENANCE)}, indent=2
                ).encode()
            if raw is not None:
                return PropulsionEvidenceSource(parts[2], raw, sha256(raw).hexdigest())
        raise RecordNotFound(
            "Propulsion validation route not found; acceptance cannot be posted."
        )
