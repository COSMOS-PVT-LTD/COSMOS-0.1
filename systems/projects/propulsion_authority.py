"""Managed propulsion commands over retained domain snapshots, not GUI state.

API injects existing editor/calculation operations. This service never imports
API/GUI/Infrastructure or changes a scientific model. Solvers run outside SQL.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from copy import deepcopy
from hashlib import sha256
from uuid import UUID, uuid5

from systems.persistence.project_repository import ProjectRepository, RecordPayload
from systems.projects.authority import (
    Head,
    HeadConflict,
    IntegrityFailure,
    Principal,
    SavedSnapshot,
    require_active_project,
)
from systems.projects.models import DERIVED_SLOT_BY_STAGE, PropulsionDesign

DOMAIN = "propulsion"


def decode_design(snapshot: SavedSnapshot) -> PropulsionDesign:
    if snapshot.domain != DOMAIN or snapshot.schema_id != "cosmos.propulsion-design.v1":
        raise IntegrityFailure("Not a supported retained propulsion snapshot.")
    design = PropulsionDesign.from_canonical_dict(json.loads(snapshot.payload))
    if (
        design.design_id != snapshot.object_id
        or design.revision != snapshot.input_revision
    ):
        raise IntegrityFailure(
            "Domain design identity/revision differs from its authority binding."
        )
    return design


class PropulsionProjectService:
    def __init__(self, repository: ProjectRepository) -> None:
        self.repository = repository

    @staticmethod
    def new_id(
        actor: Principal, project_id: str, operation_id: str, kind: str = "design"
    ) -> str:
        return str(uuid5(UUID(project_id), f"{actor.user_id}:{kind}:{operation_id}"))

    def _start(
        self, actor: Principal, project_id: str, operation_id: str, command_hash: str
    ) -> SavedSnapshot | None:
        receipt = self.repository.resolve_command(
            actor, project_id, operation_id=operation_id, command_hash=command_hash
        )
        if receipt is None:
            require_active_project(self.repository.get_project(actor, project_id))
        return receipt

    def _current(
        self, actor: Principal, project_id: str, object_id: str, expected: Head
    ) -> SavedSnapshot:
        current = self.repository.get_snapshot(
            actor, project_id, domain=DOMAIN, object_id=object_id
        )
        if current.head != expected:
            raise HeadConflict(current.head)
        return current

    def create(
        self,
        actor: Principal,
        project_id: str,
        *,
        design: PropulsionDesign,
        operation_id: str,
        command_hash: str,
    ) -> SavedSnapshot:
        replay = self._start(actor, project_id, operation_id, command_hash)
        if replay is not None:
            return replay
        candidate = PropulsionDesign.from_canonical_dict(design.to_canonical_dict())
        candidate.design_id = self.new_id(actor, project_id, operation_id)
        return self.repository.save_snapshot(
            actor,
            project_id,
            domain=DOMAIN,
            object_id=candidate.design_id,
            input_revision=candidate.revision,
            payload=RecordPayload.from_design(candidate),
            expected=Head.absent(),
            operation_id=operation_id,
            command_hash=command_hash,
            purpose="create",
        )

    def edit(
        self,
        actor: Principal,
        project_id: str,
        object_id: str,
        *,
        expected: Head,
        operation_id: str,
        command_hash: str,
        mutate: Callable[[PropulsionDesign], object],
    ) -> SavedSnapshot:
        replay = self._start(actor, project_id, operation_id, command_hash)
        if replay is not None:
            return replay
        source = self._current(actor, project_id, object_id, expected)
        candidate = decode_design(source)
        mutate(candidate)
        if candidate.design_id != object_id:
            raise IntegrityFailure(
                "Editor command cannot replace the managed design identity."
            )
        return self.repository.save_snapshot(
            actor,
            project_id,
            domain=DOMAIN,
            object_id=object_id,
            input_revision=candidate.revision,
            payload=RecordPayload.from_design(candidate),
            expected=expected,
            operation_id=operation_id,
            command_hash=command_hash,
            source_commit_id=source.commit_id,
        )

    def calculate(
        self,
        actor: Principal,
        project_id: str,
        object_id: str,
        *,
        expected: Head,
        operation_id: str,
        command_hash: str,
        parameters: Mapping[str, object],
        evaluate: Callable[[PropulsionDesign], Mapping[str, object]],
    ) -> SavedSnapshot:
        replay = self._start(actor, project_id, operation_id, command_hash)
        if replay is not None:
            return replay
        source = self._current(actor, project_id, object_id, expected)
        candidate = decode_design(source)
        # The exact captured domain snapshot already exists. Retain the actual
        # runtime parameters before starting science, including number precision.
        inputs = RecordPayload(
            json.dumps(
                {
                    "source_commit_id": source.commit_id,
                    "source_hash": source.head.content_hash,
                    "parameters": parameters,
                },
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode(),
            "cosmos.propulsion-command-input.v1",
        )
        input_commit = self.repository.save_snapshot(
            actor,
            project_id,
            domain="propulsion-inputs",
            object_id=self.new_id(actor, project_id, operation_id, "inputs"),
            input_revision=source.input_revision,
            payload=inputs,
            expected=Head.absent(),
            operation_id="input."
            + sha256(f"{actor.user_id}:{operation_id}".encode()).hexdigest(),
            command_hash=sha256((command_hash + ":inputs").encode()).hexdigest(),
            purpose="calculation_input",
            source_commit_id=source.commit_id,
        )
        response = evaluate(candidate)  # No repository transaction/lock is held.
        response_bytes = RecordPayload.from_mapping(
            response, "cosmos.propulsion-command-response.v1"
        ).data
        return self.repository.save_snapshot(
            actor,
            project_id,
            domain=DOMAIN,
            object_id=object_id,
            input_revision=candidate.revision,
            payload=RecordPayload.from_design(candidate),
            expected=expected,
            operation_id=operation_id,
            command_hash=command_hash,
            purpose="calculation",
            source_commit_id=source.commit_id,
            input_commit_id=input_commit.commit_id,
            retain_if_stale=True,
            response_payload=response_bytes,
        )

    def historical(
        self,
        actor: Principal,
        project_id: str,
        object_id: str,
        *,
        source_commit_id: str,
        expected: Head,
        operation_id: str,
        command_hash: str,
        branch: bool = False,
        name: str | None = None,
    ) -> SavedSnapshot:
        replay = self._start(actor, project_id, operation_id, command_hash)
        if replay is not None:
            return replay
        current = self._current(actor, project_id, object_id, expected)
        origin = self.repository.get_snapshot(
            actor,
            project_id,
            domain=DOMAIN,
            object_id=object_id,
            commit_id=source_commit_id,
        )
        candidate = decode_design(origin)
        if branch:
            candidate.design_id = self.new_id(actor, project_id, operation_id, "branch")
            candidate.revision = 0
            candidate.change_log = []
            candidate.name = name or f"{candidate.name} (branch)"
            candidate.created_at = candidate.updated_at
            target_expected = Head.absent()
        else:
            candidate.revision = decode_design(current).revision
            candidate.change_log = deepcopy(decode_design(current).change_log)
            target_expected = expected
        candidate.bump_revision(
            "historical_branch" if branch else "historical_activation",
            current.commit_id,
            origin.commit_id,
        )
        if branch:
            candidate.created_at = candidate.updated_at
        # Preserve old evidence in old snapshots; a new identity/input activation
        # never inherits a CURRENT result merely by copying historical status.
        for stage_id in candidate.workflow.graph.nodes:
            candidate.workflow.invalidate_from(stage_id, include_root=True)
        candidate.stamp_derived_slots_stale(tuple(DERIVED_SLOT_BY_STAGE))
        return self.repository.save_snapshot(
            actor,
            project_id,
            domain=DOMAIN,
            object_id=candidate.design_id,
            input_revision=candidate.revision,
            payload=RecordPayload.from_design(candidate),
            expected=target_expected,
            operation_id=operation_id,
            command_hash=command_hash,
            purpose="branch" if branch else "activate",
            source_commit_id=origin.commit_id,
        )
