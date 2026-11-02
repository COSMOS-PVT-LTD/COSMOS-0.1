"""Immutable downstream assessment authority; never an upstream cycle stage."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from typing import Any

from core.exceptions import CosmosError
from systems.cycle.pressure_fed import _validate
from systems.persistence.project_repository import (
    Dependency,
    ProjectRepository,
    RecordPayload,
)
from systems.projects.authority import (
    Head,
    HeadConflict,
    IntegrityFailure,
    InvalidRecord,
    Principal,
    RecordNotFound,
    SavedSnapshot,
    StoreUnavailable,
    require_active_project,
)
from systems.projects.models import PropulsionDesign
from systems.projects.propulsion_authority import DOMAIN as PROPULSION
from systems.projects.propulsion_authority import (
    PropulsionProjectService,
    decode_design,
)

DOMAIN = "pressure-fed-assessment"
INPUTS = "pressure-fed-assessment-inputs"
SCHEMA = "cosmos.managed-pressure-fed-assessment.v1"
INPUT_SCHEMA = "cosmos.managed-pressure-fed-input.v1"
Evaluator = Callable[[PropulsionDesign, dict[str, Any]], dict[str, Any]]


def payload(value: Mapping[str, Any], schema: str) -> RecordPayload:
    # Preserve admitted native float precision and nested original canonical
    # text. Core's general16-digit writer is not a second normalization step.
    try:
        raw = json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        raise InvalidRecord(
            "Pressure-fed record must be bounded finite JSON."
        ) from error
    return RecordPayload(raw, schema)


class ManagedPressureFed:
    domain = DOMAIN
    inputs_domain = INPUTS
    schema = SCHEMA
    input_schema = INPUT_SCHEMA
    operation_prefix = "pressure-fed"
    validate_specification = staticmethod(_validate)

    def __init__(
        self,
        repository: ProjectRepository,
        evaluate: Evaluator,
        methods: Callable[[], dict[str, str]],
    ) -> None:
        self.repository, self.evaluate, self.methods = repository, evaluate, methods
        self.loaded_methods = dict(methods())

    @classmethod
    def input_operation(cls, actor: Principal, operation_id: str) -> str:
        return (
            cls.operation_prefix
            + "-input."
            + sha256((actor.user_id + operation_id).encode()).hexdigest()
        )

    def create(
        self,
        actor: Principal,
        project_id: str,
        baseline_commit: str,
        expected_baseline: Head,
        specification: dict[str, Any],
        operation_id: str,
        command_hash: str,
    ) -> SavedSnapshot:
        actor.require(write=True)
        repo = self.repository
        replay = repo.resolve_command(
            actor, project_id, operation_id=operation_id, command_hash=command_hash
        )
        if replay is not None:
            if replay.domain != self.domain:
                raise InvalidRecord("Operation belongs to a different managed command.")
            return replay
        require_active_project(repo.get_project(actor, project_id))
        try:
            self.validate_specification(specification)
        except CosmosError as error:
            raise InvalidRecord(str(error)) from error
        methods = self.methods()
        if methods != self.loaded_methods:
            raise StoreUnavailable(
                "Assessment method sources changed after composition; restart before evaluation. Captured inputs are not rewritten."
            )
        input_operation = self.input_operation(actor, operation_id)
        input_hash = sha256((command_hash + ":inputs").encode()).hexdigest()
        captured = repo.resolve_command(
            actor, project_id, operation_id=input_operation, command_hash=input_hash
        )
        if captured is None:
            source = repo.resolve_snapshot(actor, project_id, baseline_commit)
            design = decode_design(source)
            current = repo.get_snapshot(
                actor, project_id, domain=PROPULSION, object_id=source.object_id
            )
            if (
                source.commit_id != current.commit_id
                or current.head != expected_baseline
            ):
                raise HeadConflict(current.head)
            object_id = PropulsionProjectService.new_id(
                actor, project_id, operation_id, self.operation_prefix
            )
            command = {
                "baseline_commit_id": baseline_commit,
                "expected_baseline": asdict(expected_baseline),
                "specification": specification,
                "operation_id": operation_id,
            }
            capture = {
                "actor_id": actor.user_id,
                "command": command,
                "baseline_commit_id": source.commit_id,
                "baseline_sha256": source.head.content_hash,
                "baseline_canonical_json": source.payload.decode(),
                "method_sources": methods,
                "scope": "Exact downstream assessment inputs; no workflow stage promotion",
            }
            captured = repo.save_snapshot(
                actor,
                project_id,
                domain=self.inputs_domain,
                object_id=object_id,
                input_revision=source.input_revision,
                payload=payload(capture, self.input_schema),
                expected=Head.absent(),
                operation_id=input_operation,
                command_hash=input_hash,
                dependencies=(Dependency("baseline", source.commit_id),),
            )
        else:
            if (
                captured.domain != self.inputs_domain
                or captured.schema_id != self.input_schema
            ):
                raise IntegrityFailure(
                    "Operation capture has an unexpected domain/schema."
                )
            capture = json.loads(captured.payload)
            if capture["method_sources"] != methods:
                raise StoreUnavailable(
                    "Captured methods differ from current runtime. Keep originals; a new explicit command is required after source reconciliation."
                )
            source = repo.resolve_snapshot(
                actor, project_id, capture["baseline_commit_id"]
            )
            if (
                source.payload.decode() != capture["baseline_canonical_json"]
                or source.head.content_hash != capture["baseline_sha256"]
            ):
                raise IntegrityFailure(
                    "Captured baseline original bytes/hash differ from authority."
                )
            design = decode_design(source)
        # Evaluate only the admitted, durably captured values, not a mutable
        # caller object. Same-operation restart may use a now-historical source.
        capture = json.loads(captured.payload)
        expected_design_text = design.to_canonical_json()
        expected_specification = deepcopy(capture["command"]["specification"])
        evaluation = None
        failure = None
        try:
            evaluation = self.evaluate(design, deepcopy(expected_specification))
            result = evaluation["result"]
            if (
                result["stage_id"] is not None
                or result["outputs"]["workflow_cycle_complete"] is not False
                or design.to_canonical_json() != expected_design_text
                or result["inputs"]["baseline_canonical_text"] != expected_design_text
                or result["inputs"]["specification"] != expected_specification
            ):
                raise IntegrityFailure(
                    "Supplemental evaluation changed its captured source or claimed cycle completion."
                )
            if self.methods() != methods:
                raise IntegrityFailure(
                    "Assessment sources changed during evaluation; no calculated answer retained."
                )
        except Exception as error:  # noqa: BLE001 - retain a failure, never success-shaped fallback
            evaluation = None
            failure = {
                "code": type(error).__name__,
                "message": str(error)[:1024],
                "action": "Inspect retained inputs/source. Start a new explicit command after correcting inputs; no answer was produced.",
            }
        record = {
            "schema": self.schema,
            "status": "COMPLETED" if failure is None else "FAILED",
            "capture_commit_id": captured.commit_id,
            **capture,
            "evaluation": evaluation,
            "failure": failure,
            "physical_validation": "NOT_PERFORMED",
            "workflow_cycle_complete": False,
        }
        return repo.save_snapshot(
            actor,
            project_id,
            domain=self.domain,
            object_id=captured.object_id,
            input_revision=captured.input_revision,
            payload=payload(record, self.schema),
            expected=Head.absent(),
            operation_id=operation_id,
            command_hash=command_hash,
            input_commit_id=captured.commit_id,
            dependencies=(
                Dependency("baseline", source.commit_id),
                Dependency("captured-inputs", captured.commit_id),
            ),
        )

    def read(self, actor: Principal, source: SavedSnapshot) -> dict[str, Any]:
        if source.domain != self.domain or source.schema_id != self.schema:
            raise InvalidRecord("Not a supported managed pressure-fed assessment.")
        value = json.loads(source.payload)
        upstream = self.repository.dependencies_current(
            actor, source.project_id, source.commit_id
        )
        methods = value["method_sources"] == self.loaded_methods == self.methods()
        return {
            "ok": True,
            "authority": {
                "project_id": source.project_id,
                "object_id": source.object_id,
                "commit_id": source.commit_id,
                "head": asdict(source.head),
                "input_revision": source.input_revision,
            },
            "record": value,
            "source_canonical_json": source.payload.decode(),
            "upstream_current": upstream and methods,
            "methods_current": methods,
            "usable_current_assessment": upstream
            and methods
            and value["status"] == "COMPLETED",
        }

    def read_input(self, actor: Principal, source: SavedSnapshot) -> dict[str, Any]:
        if source.domain != self.inputs_domain or source.schema_id != self.input_schema:
            raise InvalidRecord("Not a supported pressure-fed input capture.")
        value = json.loads(source.payload)
        try:
            terminal = self.repository.get_snapshot(
                actor, source.project_id, domain=self.domain, object_id=source.object_id
            )
        except RecordNotFound:
            terminal = None
        return {
            "ok": True,
            "authority": {
                "project_id": source.project_id,
                "object_id": source.object_id,
                "commit_id": source.commit_id,
                "head": asdict(source.head),
            },
            "capture": value,
            "source_canonical_json": source.payload.decode(),
            "terminal_commit_id": terminal.commit_id if terminal else None,
            "creator_is_actor": actor.user_id == value["actor_id"],
            "scope": "Captured inputs without terminal receipt may be in progress or interrupted; no background job/cancellation is claimed",
        }
