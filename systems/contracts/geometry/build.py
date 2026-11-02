"""Immutable job protocol/state checks; no worker, queue or artifact publication."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from ._wire import WireContract, identifier, require, unique, utc
from .artifacts import (
    Disposition,
    GeometryArtifact,
    GeometryBuildRequest,
    GeometryValidationReport,
    NamedSelection,
)
from .graph import GeometryFeatureGraph
from .snapshot import DesignSnapshot


class BuildState(str, Enum):
    DRAFT = "draft"
    VALIDATING = "validating"
    REJECTED = "rejected"
    QUEUED = "queued"
    RUNNING = "running"
    QA = "qa"
    ACCEPTED = "accepted"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"


TRANSITIONS: Mapping[BuildState, frozenset[BuildState]] = MappingProxyType({
    BuildState.DRAFT: frozenset({BuildState.VALIDATING}),
    BuildState.VALIDATING: frozenset({BuildState.REJECTED, BuildState.QUEUED}),
    BuildState.QUEUED: frozenset({BuildState.RUNNING, BuildState.CANCELLED}),
    BuildState.RUNNING: frozenset({BuildState.QA, BuildState.FAILED, BuildState.CANCEL_REQUESTED}),
    BuildState.CANCEL_REQUESTED: frozenset({BuildState.CANCELLED, BuildState.FAILED}),
    BuildState.QA: frozenset({BuildState.ACCEPTED, BuildState.REJECTED}),
    BuildState.ACCEPTED: frozenset({BuildState.PUBLISHED}),
    BuildState.REJECTED: frozenset(), BuildState.PUBLISHED: frozenset(),
    BuildState.FAILED: frozenset(), BuildState.CANCELLED: frozenset(),
})
REPEATABLE = frozenset({BuildState.QUEUED, BuildState.RUNNING, BuildState.QA, BuildState.CANCEL_REQUESTED})
FAILURE_STATES = frozenset({BuildState.REJECTED, BuildState.FAILED, BuildState.CANCELLED})


@dataclass(frozen=True, slots=True)
class GeometryBuildEvent(WireContract):
    job_id: str
    seq: int
    timestamp: str
    state: BuildState
    stage: str
    progress_fraction: float | None
    code: str | None
    message: str
    evidence_refs: tuple[str, ...]
    artifact_ids: tuple[str, ...]
    correlation_id: str

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        for name in ("job_id", "stage", "correlation_id"):
            identifier(getattr(self, name), name)
        require(self.seq >= 0, "INVALID_SEQUENCE", "Event sequence must be nonnegative")
        require(bool(self.message.strip()), "INVALID_MESSAGE", "Events require an actionable message")
        if self.code is not None:
            identifier(self.code, "code")
        if self.state in FAILURE_STATES:
            require(self.code is not None, "MISSING_DIAGNOSTIC", "Failed/rejected/cancelled events need a stable code")
        if self.progress_fraction is not None:
            require(0 <= self.progress_fraction <= 1, "INVALID_PROGRESS", "Progress must be in [0,1]; absent means unknown")
        unique(self.evidence_refs, "evidence_refs", nonempty=False)
        unique(self.artifact_ids, "artifact_ids", nonempty=False)
        require(not self.artifact_ids or self.state is BuildState.PUBLISHED, "PARTIAL_PUBLICATION", "Artifacts may be announced only by published events")
        object.__setattr__(self, "timestamp", utc(self.timestamp, "timestamp"))


def validate_events(events: tuple[GeometryBuildEvent, ...], job_id: str, correlation_id: str) -> None:
    require(bool(events) and events[0].state is BuildState.DRAFT, "INVALID_TRANSITION", "Complete transcript starts with draft")
    for index, event in enumerate(events):
        require(event.job_id == job_id and event.correlation_id == correlation_id, "JOB_MISMATCH", "Event job/correlation identity mismatch")
        require(event.seq == index, "INVALID_SEQUENCE", "Complete transcript must have contiguous increasing sequence numbers from zero")
        if index:
            previous = events[index - 1]
            require(event.timestamp >= previous.timestamp, "INVALID_TIMESTAMP", "Event timestamps moved backward")
            allowed = event.state in TRANSITIONS[previous.state] or (event.state == previous.state and event.state in REPEATABLE)
            require(allowed, "INVALID_TRANSITION", "Invalid or terminal build transition")
            if event.state == previous.state and event.progress_fraction is not None and previous.progress_fraction is not None:
                require(event.progress_fraction >= previous.progress_fraction, "INVALID_PROGRESS", "Progress within a lifecycle state must not move backward")


@dataclass(frozen=True, slots=True)
class GeometryBuildRecord(WireContract):
    """Candidates are not published unless the entire transcript/gate agrees."""
    job_id: str
    request: GeometryBuildRequest
    snapshot: DesignSnapshot
    feature_graph: GeometryFeatureGraph
    events: tuple[GeometryBuildEvent, ...]
    artifacts: tuple[GeometryArtifact, ...]
    named_selections: tuple[NamedSelection, ...]
    reports: tuple[GeometryValidationReport, ...]

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        identifier(self.job_id, "job_id")
        self.feature_graph.validate_snapshot(self.snapshot)
        require(self.request.snapshot_id == self.snapshot.snapshot_id
                and self.request.feature_graph_id == self.feature_graph.graph_id
                and self.request.feature_graph_sha256 == self.feature_graph.content_sha256,
                "STALE_REQUEST", "Request snapshot/graph lineage mismatch")
        require(self.request.frame_id in {f.frame_id for f in self.snapshot.frames}, "UNKNOWN_FRAME", "Request frame is undefined")
        by_feature = {f.feature_id: f for f in self.feature_graph.features}
        require(all(f.representation == self.request.representation for f in by_feature.values()),
                "REPRESENTATION_MISMATCH", "V1 graphs are representation-homogeneous; no silent conversion")
        validate_events(self.events, self.job_id, self.request.correlation_id)
        unique(tuple(a.artifact_id for a in self.artifacts), "artifacts", nonempty=False)
        require(len({a.storage_uri for a in self.artifacts}) == len(self.artifacts), "DUPLICATE_ARTIFACT", "Artifacts cannot share a storage path")
        require(len({a.geometry_revision_id for a in self.artifacts}) <= 1, "ARTIFACT_LINEAGE", "One build cannot publish mixed geometry revisions")
        unique(tuple(s.semantic_id for s in self.named_selections), "named_selections", nonempty=False)
        unique(tuple(r.report_id for r in self.reports), "reports", nonempty=False)
        for artifact in self.artifacts:
            require(artifact.job_id == self.job_id and artifact.snapshot_id == self.snapshot.snapshot_id
                    and artifact.feature_graph_sha256 == self.feature_graph.content_sha256, "ARTIFACT_LINEAGE", "Artifact job/snapshot/graph lineage mismatch")
            for name in ("backend_id", "backend_version", "representation", "approximation_profile", "frame_id", "source_tolerance_m", "export_tolerance_m", "voxel_resolution_m"):
                require(getattr(artifact, name) == getattr(self.request, name), "ARTIFACT_LINEAGE", "Artifact silently changed request settings", name)
            require(artifact.output_format in self.request.output_formats, "FORMAT_MISMATCH", "Artifact format was not requested")
        for selection in self.named_selections:
            matches = [a for a in self.artifacts if a.geometry_revision_id == selection.geometry_revision_id]
            require(bool(matches), "STALE_SELECTION", "No candidate artifact matches selection revision")
            selection.validate_binding(self.feature_graph, matches[0])
        require(self.state not in FAILURE_STATES or not self.artifacts, "PARTIAL_PUBLICATION", "Failed/rejected/cancelled job cannot retain publishable artifacts")
        if self.state in {BuildState.ACCEPTED, BuildState.PUBLISHED}:
            require(bool(self.artifacts), "MISSING_QA", "Accepted state needs candidate artifacts and independently accepted QA")
            for artifact in self.artifacts:
                reports = [r for r in self.reports if r.report_id == artifact.topology_report_id and r.artifact_id == artifact.artifact_id]
                require(len(reports) == 1 and reports[0].disposition is Disposition.ACCEPTED,
                        "QA_NOT_ACCEPTED", "Acceptance requires matching independently accepted QA")
                require({"topology", "dimensions", "export_round_trip"} <= {c.check_id for c in reports[0].checks},
                        "MISSING_QA", "Acceptance requires topology, dimensional and independent export round-trip records")
        if self.state is BuildState.PUBLISHED:
            require(bool(self.artifacts) and set(self.events[-1].artifact_ids) == {a.artifact_id for a in self.artifacts},
                    "PARTIAL_PUBLICATION", "Published event must announce all and only manifest artifacts")
            require({a.output_format for a in self.artifacts} == set(self.request.output_formats), "PARTIAL_PUBLICATION", "Published manifest omitted requested output formats")
            for artifact in self.artifacts:
                reports = [r for r in self.reports if r.report_id == artifact.topology_report_id and r.artifact_id == artifact.artifact_id]
                require(reports[0].report_id in self.events[-1].evidence_refs, "MISSING_QA", "Published event must link acceptance evidence")

    @property
    def state(self) -> BuildState:
        return self.events[-1].state

    @property
    def published_artifacts(self) -> tuple[GeometryArtifact, ...]:
        return self.artifacts if self.state is BuildState.PUBLISHED else ()

    def export_eligibility(self, active_snapshot: DesignSnapshot, active_graph: GeometryFeatureGraph) -> tuple[bool, tuple[str, ...]]:
        active_graph.validate_snapshot(active_snapshot)
        reasons = []
        if self.state is not BuildState.PUBLISHED:
            reasons.append("NOT_PUBLISHED")
        if self.snapshot.snapshot_id != active_snapshot.snapshot_id or self.feature_graph.content_sha256 != active_graph.content_sha256:
            reasons.append("STALE_DEPENDENCY")
        if self.snapshot.project_id != active_snapshot.project_id:
            reasons.append("PROJECT_MISMATCH")
        return not reasons, tuple(reasons)
