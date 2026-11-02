"""Reversible project-scoped CAD development selection, never engineering release.

Old source blobs/heads stay intact. A single compare-and-swap selection record
changes which exact geometry intent the workspace opens by default. Historical
calculations and generated artifacts are not rebound to the selected candidate.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid5

from systems.geometry.component_authority import DOMAIN as COMPONENT_DOMAIN
from systems.geometry.engine_redesign_authority import DOMAIN as CANDIDATE_DOMAIN
from systems.geometry.engine_redesign_authority import methods as candidate_methods
from systems.persistence.project_repository import Dependency, RecordPayload
from systems.projects.authority import (
    Head,
    HeadConflict,
    InvalidRecord,
    RecordNotFound,
    StoreUnavailable,
)

DOMAIN = "engine-development-baseline"
SCHEMA = "cosmos.engine-development-baseline.v1"


def selection(source):
    return {
        "kind": "COMPACT_CANDIDATE"
        if source.domain == CANDIDATE_DOMAIN
        else "RETAINED_COMPONENT",
        "domain": source.domain,
        "object_id": source.object_id,
        "commit_id": source.commit_id,
        "head": asdict(source.head),
    }


def methods():
    path = Path(__file__).resolve()
    return {
        **candidate_methods(),
        "systems/geometry/development_baseline.py": sha256(
            path.read_bytes()
        ).hexdigest(),
    }


class DevelopmentBaselines:
    def __init__(self, redesigns):
        self.redesigns = redesigns
        self.repository = redesigns.repository
        self.loaded_methods = methods()

    @staticmethod
    def object_id(project):
        return str(uuid5(UUID(project), "cosmos.engine-development-baseline"))

    def _stable(self):
        if self.loaded_methods != methods():
            raise StoreUnavailable(
                "Development selection methods changed; reload before a new selection"
            )

    def _latest(self, actor, project):
        self.repository.get_project(actor, project)
        try:
            return self.repository.get_snapshot(
                actor, project, domain=DOMAIN, object_id=self.object_id(project)
            )
        except RecordNotFound:
            return None

    def current(self, actor, project):
        saved = self._latest(actor, project)
        return (
            self.envelope(actor, saved)
            if saved
            else {
                "ok": True,
                "baseline": None,
                "expected": asdict(Head.absent()),
                "scope": "No development geometry selection installed; no baseline was changed",
            }
        )

    def _source(self, actor, project, selected):
        source = self.repository.get_snapshot(
            actor,
            project,
            domain=selected["domain"],
            object_id=selected["object_id"],
            commit_id=selected["commit_id"],
        )
        if asdict(source.head) != selected["head"]:
            raise InvalidRecord("Baseline selection source hash/head mismatch")
        if source.domain == CANDIDATE_DOMAIN:
            envelope = self.redesigns.envelope(actor, source)
            usable = envelope["upstream_current"]
            value = envelope["record"]
            component = self.repository.resolve_snapshot(
                actor, project, value["source_commit_id"]
            )
        elif source.domain == COMPONENT_DOMAIN:
            usable = self.redesigns.components.models.current(actor, source)
            component = source
        else:
            raise InvalidRecord(
                "Only an exact compact candidate or retained component may be a CAD development baseline"
            )
        return source, component, usable

    def _write(
        self,
        actor,
        project,
        selected,
        *,
        expected,
        operation_id,
        command_hash,
        reason,
        action,
    ):
        actor.require(write=True)
        self._stable()
        replay = self.repository.resolve_command(
            actor, project, operation_id=operation_id, command_hash=command_hash
        )
        if replay is not None:
            if replay.domain != DOMAIN or replay.object_id != self.object_id(project):
                raise InvalidRecord(
                    "Replayed operation is not this project's development selection"
                )
            return self.envelope(actor, replay)
        prior = self._latest(actor, project)
        actual = prior.head if prior else Head.absent()
        if expected != actual:
            raise HeadConflict(actual)
        if type(reason) is not str or not 0 < len(reason.strip()) <= 1000:
            raise InvalidRecord(
                "An explicit bounded reason is required; selection is not engineering approval"
            )
        source, component, usable = self._source(actor, project, selected)
        if not usable:
            raise InvalidRecord(
                "Selected geometry or its upstream source is stale/historical; reconcile before changing the development baseline"
            )
        source_value = json.loads(component.payload)
        previous = (
            json.loads(prior.payload)["selection"] if prior else selection(component)
        )
        value = {
            "selection": selected,
            "previous_selection": previous,
            "previous_baseline_commit_id": prior.commit_id if prior else None,
            "component_source": selection(component),
            "propulsion_commit_id": source_value["baseline_commit_id"],
            "reason": reason.strip(),
            "action": action,
            "method_sources": self.loaded_methods,
            "source_retention": "RETAINED_IMMUTABLE_NOT_DELETED",
            "selection_scope": "PRELIMINARY_GEOMETRY_DEVELOPMENT_ONLY",
            "native_generation": "NOT_ESTABLISHED_BY_SELECTION",
            "matched_physics": "REQUIRES_CANDIDATE_MATCHED_RECOMPUTATION",
            "engineering_acceptance": "NOT_PERFORMED",
            "physical_validation": "NOT_PERFORMED",
            "r08": "ON_HOLD",
        }
        dependencies = [Dependency("selected-geometry", source.commit_id)]
        if source.commit_id != component.commit_id:
            dependencies.append(
                Dependency("retained-component-source", component.commit_id)
            )
        saved = self.repository.save_snapshot(
            actor,
            project,
            domain=DOMAIN,
            object_id=self.object_id(project),
            input_revision=0 if prior is None else prior.input_revision + 1,
            payload=RecordPayload.from_mapping(
                value, SCHEMA, source_namespace=component.source_namespace
            ),
            expected=expected,
            operation_id=operation_id,
            command_hash=command_hash,
            dependencies=tuple(dependencies),
            purpose="activate",
        )
        # Recheck after persistence. A concurrent upstream edit must never be
        # reported as CURRENT, even if it raced the pre-save applicability check.
        return self.envelope(actor, saved)

    def activate(
        self,
        actor,
        project,
        *,
        candidate_commit_id,
        expected_candidate,
        expected,
        operation_id,
        command_hash,
        reason,
    ):
        actor.require(write=True)
        self._stable()
        candidate = self.repository.resolve_snapshot(
            actor, project, candidate_commit_id
        )
        if candidate.domain != CANDIDATE_DOMAIN:
            raise InvalidRecord(
                "Development activation requires an exact compact candidate in this authorized project"
            )
        if candidate.head != expected_candidate:
            raise HeadConflict(candidate.head)
        return self._write(
            actor,
            project,
            selection(candidate),
            expected=expected,
            operation_id=operation_id,
            command_hash=command_hash,
            reason=reason,
            action="SELECT_COMPACT_DEVELOPMENT_BASELINE",
        )

    def rollback(self, actor, project, *, expected, operation_id, command_hash, reason):
        actor.require(write=True)
        self._stable()
        replay = self.repository.resolve_command(
            actor, project, operation_id=operation_id, command_hash=command_hash
        )
        if replay is not None:
            if replay.domain != DOMAIN or replay.object_id != self.object_id(project):
                raise InvalidRecord(
                    "Operation does not identify this project's baseline"
                )
            return self.envelope(actor, replay)
        prior = self._latest(actor, project)
        if prior is None:
            raise RecordNotFound("No development baseline selection exists to undo")
        return self._write(
            actor,
            project,
            json.loads(prior.payload)["previous_selection"],
            expected=expected,
            operation_id=operation_id,
            command_hash=command_hash,
            reason=reason,
            action="RESTORE_PREVIOUS_DEVELOPMENT_SELECTION",
        )

    def envelope(self, actor, saved):
        value = json.loads(saved.payload)
        source, _, usable = self._source(actor, saved.project_id, value["selection"])
        latest = self._latest(actor, saved.project_id)
        current = (
            usable
            and latest.commit_id == saved.commit_id
            and value["method_sources"] == self.loaded_methods == methods()
            and self.repository.dependencies_current(
                actor, saved.project_id, saved.commit_id
            )
        )
        return {
            "ok": True,
            "baseline": {
                "authority": {
                    "project_id": saved.project_id,
                    "object_id": saved.object_id,
                    "commit_id": saved.commit_id,
                    "head": asdict(saved.head),
                    "input_revision": saved.input_revision,
                },
                "record": value,
                "upstream_current": current,
                "selected_geometry_head": asdict(source.head),
                "engineering_acceptance": "NOT_PERFORMED",
            },
            "expected": asdict(latest.head),
        }

    def history(self, actor, project):
        if self._latest(actor, project) is None:
            return {"ok": True, "baselines": []}
        ids = self.repository.list_commit_ids(
            actor, project, domain=DOMAIN, object_id=self.object_id(project), limit=50
        )
        return {
            "ok": True,
            "baselines": [
                self.envelope(
                    actor, self.repository.resolve_snapshot(actor, project, key)
                )["baseline"]
                for key in ids
            ],
        }
