"""Engine-source durable nozzle builds over the existing R05 coordinator."""

from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid5

from plugins.geometry.nozzle_protocol import VERSION, profile, validate
from systems.contracts.geometry import (
    DesignSnapshot,
    GeometryBuildRequest,
    GeometryFeatureGraph,
    OutputFormat,
    Representation,
)
from systems.geometry.authority import ManagedGeometry
from systems.geometry.nozzle_qa import NozzleQALimits
from systems.geometry.nozzle_reference import NozzleReference
from systems.geometry.workbench import Revision
from systems.persistence.project_repository import Dependency, RecordPayload
from systems.projects.authority import (
    AccessDenied,
    Head,
    HeadConflict,
    InvalidRecord,
    RecordNotFound,
    SavedSnapshot,
    StoreUnavailable,
)

DOMAIN = "engine-nozzle-build"
SCHEMA = "cosmos.engine-nozzle-build-input.v1"


def methods() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    files = {
        "systems/geometry/engine_builds.py", "systems/geometry/authority.py", "systems/geometry/service.py", "systems/geometry/qa.py",
        "systems/geometry/nozzle_qa.py", "systems/geometry/nozzle_reference.py", "systems/geometry/nozzle_workspace.py",
        "plugins/geometry/nozzle_protocol.py", "plugins/geometry/nozzle_adapter.py", "plugins/geometry/protocol.py", "plugins/geometry/adapters.py",
        "plugins/geometry/workers/nozzle_worker.py", "plugins/geometry/workers/nozzle_step_reader.py", "plugins/geometry/workers/stl_encoding.py",
        "api/nozzle_geometry.py", "infrastructure/persistence/durable_jobs.py", "infrastructure/geometry/supervisor.py",
    }
    files.update(str(p.relative_to(root)) for directory in ("core", "systems/contracts/geometry") for p in (root / directory).rglob("*.py"))
    return {name: sha256((root / name).read_bytes()).hexdigest() for name in sorted(files)}


def decode(source: SavedSnapshot) -> Revision:
    if source.domain != DOMAIN or source.schema_id != SCHEMA or not source.source_namespace.startswith("engine-design-"):
        raise InvalidRecord("Exact engine nozzle build-input domain/schema/namespace required.")
    value = json.loads(source.payload)
    snapshot = DesignSnapshot.from_json(value["snapshot_json"])
    graph = GeometryFeatureGraph.from_json(value["graph_json"])
    request = GeometryBuildRequest.from_json(value["request_json"])
    validate(request, snapshot, graph)
    if snapshot.project_id != source.source_namespace:
        raise InvalidRecord("Engine build namespace differs from its immutable source.")
    NozzleQALimits.from_spec(value["qa_specification"])
    return Revision(value, snapshot, graph, request)


class EngineBuildCoordinator(ManagedGeometry):
    def __init__(self, repository, jobs, factory, resolve_actor, intent_service):
        super().__init__(repository, jobs, dict, resolve_actor)
        self.factory, self.intent_service = factory, intent_service
        self.loaded_methods = methods()

    def current(self, actor, source) -> bool:
        value = json.loads(source.payload)
        return (self.repository.dependencies_current(actor, source.project_id, source.commit_id)
                and value["method_sources"] == self.loaded_methods == methods()
                and self.intent_service.read(actor, self.repository.resolve_snapshot(actor, source.project_id, value["intent_commit_id"]))["upstream_current"])

    def runtime_current(self, source) -> bool:
        try:
            return json.loads(source.payload)["runtime_hashes"] == self.factory().runtime_hashes
        except (ValueError, OSError, RuntimeError, StoreUnavailable):
            # Runtime removal/change must not erase previously retained originals
            # or turn a real completed candidate into a storage failure.
            return False

    def capture(self, actor, project, intent_commit, expected, qa_specification, operation_id, command_hash):
        actor.require(write=True)
        operation = "engine-build-input." + sha256((actor.user_id + operation_id).encode()).hexdigest()
        capture_hash = sha256((command_hash + ":input").encode()).hexdigest()
        prior = self.repository.resolve_command(actor, project, operation_id=operation, command_hash=capture_hash)
        if prior is not None:
            if prior.domain != DOMAIN:
                raise InvalidRecord("Capture operation belongs to another domain.")
            return prior
        intent = self.repository.resolve_snapshot(actor, project, intent_commit)
        envelope = self.intent_service.read(actor, intent)
        if not envelope["usable_current_assessment"]:
            raise InvalidRecord("Create/select a CURRENT successful engine intent with current baseline/method sources first; no latest-source substitution.")
        current = self.repository.get_snapshot(actor, project, domain=intent.domain, object_id=intent.object_id)
        if intent.commit_id != current.commit_id or expected != intent.head:
            raise HeadConflict(current.head)
        if methods() != self.loaded_methods:
            raise StoreUnavailable("Engine build method sources changed after loading; restart before new admission.")
        NozzleQALimits.from_spec(qa_specification)
        output = envelope["record"]["evaluation"]["result"]["outputs"]
        snapshot = DesignSnapshot.from_json(output["snapshot_json"])
        graph = GeometryFeatureGraph.from_json(output["graph_json"])
        object_id = str(uuid5(UUID(project), actor.user_id + ":engine-nozzle-build:" + operation_id))
        request = GeometryBuildRequest("request-" + object_id, snapshot.snapshot_id, graph.graph_id, graph.content_sha256,
                    "occt", VERSION, Representation.ANALYTIC_BREP, "none", output["source_tolerance_m"], output["export_tolerance_m"], None,
                    (OutputFormat.STEP, OutputFormat.STL), snapshot.frame_id, "build-" + object_id)
        validate(request, snapshot, graph)
        # Trusted runtime configuration is checked before admitting a command;
        # no client worker path, timeout, environment or code is accepted.
        workspace = self.factory()
        value = {"intent_commit_id": intent.commit_id, "intent_sha256": intent.head.content_hash, "intent_canonical_json": intent.payload.decode(),
                 "snapshot_json": snapshot.to_json(), "graph_json": graph.to_json(), "request_json": request.to_json(),
                 "qa_specification": qa_specification, "method_sources": self.loaded_methods, "runtime_hashes": workspace.runtime_hashes,
                 "command": {"intent_commit_id": intent.commit_id, "expected_intent": asdict(expected), "qa_specification": qa_specification, "output_formats": ["step", "stl"], "operation_id": operation_id},
                 "scope": "Engine-derived software-QA candidate, not engineering/physical acceptance"}
        return self.repository.save_snapshot(actor, project, domain=DOMAIN, object_id=object_id, input_revision=intent.input_revision,
                    payload=RecordPayload(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(), SCHEMA, snapshot.project_id),
                    expected=Head.absent(), operation_id=operation, command_hash=capture_hash, dependencies=(Dependency("engine-intent", intent.commit_id),))

    def decode(self, source):
        revision = decode(source)
        if revision.settings["method_sources"] != self.loaded_methods or methods() != self.loaded_methods:
            raise StoreUnavailable("Exact captured build methods are no longer loaded/current; preserve originals and capture a new command after reconciliation.")
        return revision

    def select_service(self, revision):
        workspace = self.factory()
        if revision.settings["runtime_hashes"] != workspace.runtime_hashes:
            raise StoreUnavailable("Native runtime differs from captured build originals; no silent retry with changed libraries/configuration.")
        return workspace.service_for(NozzleQALimits.from_spec(revision.settings["qa_specification"]))

    def reference(self, revision):
        return NozzleReference(profile(revision.snapshot, revision.graph))

    def selection_allowed(self, actor, job):
        try:
            source = self.repository.resolve_snapshot(actor, job.project_id, job.source_commit_id)
            return self.current(actor, source) and self.runtime_current(source)
        except (AccessDenied, RecordNotFound):
            return False
