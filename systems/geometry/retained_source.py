"""Immutable admitted fixture inputs, not a new geometry builder/authority."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from plugins.geometry.protocol import checked_file
from systems.contracts.geometry import BuildState, GeometryBuildRecord
from systems.contracts.geometry._wire import require
from systems.geometry.authority import decode_source
from systems.geometry.service import VerifiedCandidate
from systems.geometry.workbench import Revision
from systems.persistence.job_repository import BlobAttachment, JobRepository, JobState
from systems.persistence.project_repository import ProjectRepository
from systems.projects.authority import Principal


@dataclass(frozen=True)
class RetainedFixture:
    actor: str
    job_id: str
    commit_id: str
    revision: Revision
    record: GeometryBuildRecord
    evidence_json: str
    files: tuple[BlobAttachment, ...]


def retained_fixture(repo: ProjectRepository, jobs: JobRepository, actor: Principal, project_id: str, job_id: str) -> RetainedFixture:
    job = jobs.get(actor, project_id, job_id)
    require(job.domain == "geometry-fixture" and job.state is JobState.COMPLETED and job.selected and job.current_input,
            "STALE_GEOMETRY", "Use an exact selected/current completed fixture in this owning project")
    source = repo.get_snapshot(actor, project_id, domain=job.domain, object_id=job.object_id, commit_id=job.source_commit_id)
    revision = decode_source(source)
    require(revision.settings["backend"] == "occt" and revision.settings["operation"] == "sphere", "UNQUALIFIED_HANDOFF", "Only the existing OCCT sphere radial benchmark is supported")
    value = json.loads(job.payload)
    require(set(value) == {"record_json", "evidence_json"}, "SOURCE_UNAVAILABLE", "Original native record/QA required")
    record = GeometryBuildRecord.from_json(value["record_json"])
    require(record.snapshot == revision.snapshot and record.feature_graph == revision.graph and record.request == revision.request
            and record.state is BuildState.ACCEPTED and len(record.artifacts) == 1 and record.artifacts[0].output_format.value == "step",
            "PROVENANCE_MISMATCH", "Original accepted native record must bind the captured study geometry")
    qa = json.loads(value["evidence_json"])
    require(qa["qa-step"]["pass"] is True, "QA_REJECTED", "Original accepted STEP reimport evidence required")
    artifact = record.artifacts[0]
    expected = {"source.brep": artifact.source_artifact_sha256, Path(artifact.storage_uri).name: artifact.sha256}
    require(set(expected) == {"source.brep", "export.step"}, "UNQUALIFIED_HANDOFF", "Only fixed supported source filenames may be materialized")
    blobs = tuple(BlobAttachment(name, jobs.blob(actor, project_id, job_id, name), digest,
        "source" if name == "source.brep" else "artifact") for name, digest in expected.items())
    for blob in blobs:
        require(hashlib.sha256(blob.data).hexdigest() == blob.content_hash, "SOURCE_CORRUPT", "Retained native source bytes differ")
    return RetainedFixture(actor.user_id, job_id, source.commit_id, revision, record, value["evidence_json"], blobs)


class CapturedGeometrySource:
    """Worker-local captured source. Global freshness comes from durable lineage.

    It cannot read another project or substitute the latest native session. No
    selection/publication methods exist; exact files are checked on every use.
    """
    def __init__(self, source: RetainedFixture, directory: Path) -> None:
        self.source = source
        self.candidate = VerifiedCandidate(source.record, directory, source.evidence_json)

    def accepted(self, actor: str, job: str, snapshot: str) -> tuple[Revision, VerifiedCandidate]:
        source = self.source
        require(actor == source.actor and job == source.job_id and snapshot == source.revision.snapshot.snapshot_id,
                "SOURCE_SCOPE", "Worker input must match its admitted actor/job/snapshot")
        for blob in source.files:
            checked_file(self.candidate.directory, blob.name, blob.content_hash)
        return source.revision, self.candidate

    def context(self, actor: str) -> dict[str, Any]:
        self.accepted(actor, self.source.job_id, self.source.revision.snapshot.snapshot_id)
        return {"snapshot": json.loads(self.source.revision.snapshot.to_json()), "scope": "captured-admitted-worker-input-only"}
