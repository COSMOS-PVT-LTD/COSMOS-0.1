"""CAS-managed isolated redesign revisions, subordinate to exact component sources."""

from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from systems.geometry.component_authority import DOMAIN as SOURCE_DOMAIN
from systems.geometry.component_authority import from_source
from systems.geometry.component_authority import methods as component_methods
from systems.geometry.component_interfaces import methods as interface_methods
from systems.geometry.engine_redesign import SCHEMA, compile_candidate, suggest
from systems.persistence.project_repository import Dependency, RecordPayload
from systems.projects.authority import (
    Head,
    HeadConflict,
    InvalidRecord,
    StoreUnavailable,
)

DOMAIN = "engine-redesign-candidate"


def methods():
    root = Path(__file__).resolve().parents[2]
    files = (
        "systems/geometry/engine_redesign.py",
        "systems/geometry/engine_redesign_authority.py",
        "api/engine_redesign.py",
    )
    return {
        **component_methods(),
        **interface_methods(),
        **{n: sha256((root / n).read_bytes()).hexdigest() for n in files},
    }


class Redesigns:
    def __init__(self, components):
        self.components = components
        self.repository = components.repository
        self.loaded_methods = methods()

    def _stable(self):
        if methods() != self.loaded_methods:
            raise StoreUnavailable(
                "Redesign methods changed; reload backend before creating new provenance"
            )

    def source(self, actor, project, commit, expected=None):
        self._stable()
        source = self.repository.resolve_snapshot(actor, project, commit)
        if source.domain != SOURCE_DOMAIN:
            raise InvalidRecord(
                "Exact saved component-model source required in the same authorized project"
            )
        if expected is not None and source.head != expected:
            raise HeadConflict(source.head)
        if not self.components.models.current(actor, source):
            raise InvalidRecord(
                "Source component model is historical/stale; explicitly reconcile it before deriving a new candidate"
            )
        return source

    def seed(self, actor, project, commit):
        source = self.source(actor, project, commit)
        specification = suggest(from_source(source))
        return {
            "ok": True,
            "persisted": False,
            "source_commit_id": source.commit_id,
            "expected_source": asdict(source.head),
            "specification": specification,
            "inspection": compile_candidate(
                from_source(source), specification
            ).report(),
        }

    def preview(self, actor, project, commit, specification):
        source = self.source(actor, project, commit)
        candidate = compile_candidate(from_source(source), specification)
        return {
            "ok": True,
            "persisted": False,
            "source_commit_id": source.commit_id,
            "expected_source": asdict(source.head),
            "inspection": candidate.report(),
            "recipe": candidate.wire(),
        }

    def save(
        self, actor, project, object_id, body, expected, expected_source, command_hash
    ):
        actor.require(write=True)
        self._stable()
        replay = self.repository.resolve_command(
            actor, project, operation_id=body["operation_id"], command_hash=command_hash
        )
        if replay is not None:
            return replay
        source = self.source(actor, project, body["source_commit_id"], expected_source)
        title = body["title"]
        if type(title) is not str or not 0 < len(title.strip()) <= 240:
            raise InvalidRecord("A bounded explicit candidate title is required")
        prior = (
            None
            if expected == Head.absent()
            else self.repository.get_snapshot(
                actor, project, domain=DOMAIN, object_id=object_id
            )
        )
        if prior is not None and prior.head != expected:
            raise HeadConflict(prior.head)
        candidate = compile_candidate(from_source(source), body["specification"])
        value = {
            "title": title,
            "specification": candidate.specification,
            "source_commit_id": source.commit_id,
            "source_object_id": source.object_id,
            "source_sha256": source.head.content_hash,
            "source_canonical_json": source.payload.decode(),
            "method_sources": self.loaded_methods,
            "inspection": candidate.report(),
            "recipe_sha256": candidate.wire()["recipe_sha256"],
            "acceptance": "NOT_PERFORMED",
            "r08": "ON_HOLD",
            "baseline_replacement": False,
        }
        return self.repository.save_snapshot(
            actor,
            project,
            domain=DOMAIN,
            object_id=object_id,
            input_revision=0 if prior is None else prior.input_revision + 1,
            payload=RecordPayload.from_mapping(
                value, SCHEMA, source_namespace=candidate.plan.snapshot.project_id
            ),
            expected=expected,
            operation_id=body["operation_id"],
            command_hash=command_hash,
            dependencies=(Dependency("component-source", source.commit_id),),
            purpose="create" if prior is None else "save",
        )

    def envelope(self, actor, saved):
        value = json.loads(saved.payload)
        source = self.repository.resolve_snapshot(
            actor, saved.project_id, value["source_commit_id"]
        )
        current = (
            self.repository.get_snapshot(
                actor, saved.project_id, domain=DOMAIN, object_id=saved.object_id
            ).commit_id
            == saved.commit_id
            and value["method_sources"] == self.loaded_methods == methods()
            and self.components.models.current(actor, source)
            and self.repository.dependencies_current(
                actor, saved.project_id, saved.commit_id
            )
        )
        return {
            "ok": True,
            "authority": {
                "project_id": saved.project_id,
                "object_id": saved.object_id,
                "commit_id": saved.commit_id,
                "head": asdict(saved.head),
                "input_revision": saved.input_revision,
            },
            "record": value,
            "upstream_current": current,
            "acceptance": "NOT_PERFORMED",
        }
