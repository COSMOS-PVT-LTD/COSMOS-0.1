"""Incremental native transcript retention; synthetic events are not kernel QA."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import replace

import pytest

from infrastructure.persistence.durable_jobs import SQLiteJobRepository, message
from infrastructure.persistence.inventory import inventory
from infrastructure.persistence.schema import APPLICATION_ID, SCHEMA_V3
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.contracts.geometry import (
    BuildState,
    GeometryBuildEvent,
    GeometryContractError,
)
from systems.geometry.authority import source_payload
from systems.geometry.workbench import GeometryWorkbench
from systems.persistence.job_repository import JobState
from systems.persistence.project_repository import RecordPayload
from systems.projects.authority import (
    AccessDenied,
    Head,
    IntegrityFailure,
    InvalidRecord,
    Principal,
    QuotaExceeded,
    RecordNotFound,
    SchemaMismatch,
)

OWNER = Principal("USR-stage-owner", "ENGINEER")


@pytest.fixture
def stage_setup(tmp_path):
    repo = SQLiteProjectRepository(tmp_path / "root")
    jobs = SQLiteJobRepository(repo)
    project = repo.create_project(OWNER, title="Stage software fixture", mission="Not native QA", operation_id="project")
    revision = GeometryWorkbench.revision({"operation": "sphere", "backend": "occt", "voxel_m": .0005})
    source = repo.save_snapshot(OWNER, project.project_id, domain="geometry-fixture", object_id="fixture", input_revision=0,
        payload=source_payload(revision), expected=Head.absent(), operation_id="input")
    job = jobs.admit(OWNER, source, operation_id="admit", request_hash="1"*64)
    jobs.advance(job.job_id, JobState.RUNNING, message("RUNNING"))
    return repo, jobs, project, job, revision


def event(revision, sequence=0, state=BuildState.DRAFT):
    return GeometryBuildEvent("native-test", sequence, "2026-10-18T00:00:00+00:00", state, state.value,
        None, "TEST_FAILURE" if state is BuildState.FAILED else None, "Synthetic event only", (), (), revision.request.correlation_id)


def payload(value):
    return RecordPayload(value.to_json().encode(), "cosmos.geometry-stage.v1", "p07-software-fixtures")


def test_prefix_survives_restart_recovery_and_exact_retry(stage_setup):
    repo, jobs, project, job, revision = stage_setup
    values = [event(revision), event(revision, 1, BuildState.VALIDATING)]
    receipts = [jobs.append_stage(job.job_id, payload(value)) for value in values]
    reopened = SQLiteJobRepository(SQLiteProjectRepository(repo.files.root))
    assert reopened.recover() == 1
    assert reopened.get(OWNER, project.project_id, job.job_id).state is JobState.INTERRUPTED
    assert reopened.list_stages(OWNER, project.project_id, job.job_id) == tuple(receipts)
    for value, receipt in zip(values, receipts):
        assert reopened.stage_source(OWNER, project.project_id, job.job_id, value.seq) == value.to_json().encode()
        assert reopened.append_stage(job.job_id, payload(value)) == receipt
    with pytest.raises(InvalidRecord):
        reopened.append_stage(job.job_id, payload(event(revision, 2, BuildState.QUEUED)))


def test_exact_stage_retry_cannot_bypass_admitted_namespace(stage_setup):
    _repo, jobs, _project, job, revision = stage_setup
    original = payload(event(revision))
    jobs.append_stage(job.job_id, original)
    with pytest.raises(InvalidRecord, match="domain/schema/namespace"):
        jobs.append_stage(job.job_id, RecordPayload(original.data, original.schema_id, "engine-design-foreign"))


@pytest.mark.parametrize("change", ["sequence", "state", "correlation", "native-id", "time", "bytes"])
def test_invalid_prefix_and_nonidentical_retry_fail_closed(stage_setup, change):
    _repo, jobs, project, job, revision = stage_setup
    first = event(revision)
    jobs.append_stage(job.job_id, payload(first))
    second = event(revision, 1, BuildState.VALIDATING)
    value = {"sequence": replace(second, seq=3), "state": replace(second, state=BuildState.QUEUED),
        "correlation": replace(second, correlation_id="other"), "native-id": replace(second, job_id="other"),
        "time": replace(second, timestamp="2026-10-17T00:00:00+00:00"), "bytes": replace(first, message="different")}[change]
    with pytest.raises((GeometryContractError, InvalidRecord)):
        jobs.append_stage(job.job_id, payload(value))
    assert len(jobs.list_stages(OWNER, project.project_id, job.job_id)) == 1


def test_stage_scope_paging_and_corruption(stage_setup):
    repo, jobs, project, job, revision = stage_setup
    receipt = jobs.append_stage(job.job_id, payload(event(revision)))
    other = Principal("USR-other", "ENGINEER")
    with pytest.raises(AccessDenied):
        jobs.list_stages(other, project.project_id, job.job_id)
    foreign = repo.create_project(OWNER, title="Other project", mission="Scope", operation_id="other")
    with pytest.raises(RecordNotFound):
        jobs.stage_source(OWNER, foreign.project_id, job.job_id, 0)
    with pytest.raises(RecordNotFound):
        jobs.stage_source(OWNER, project.project_id, job.job_id, 1)
    with pytest.raises(InvalidRecord):
        jobs.list_stages(OWNER, project.project_id, job.job_id, limit=101)
    (repo.files.blobs / receipt.content_hash).write_bytes(b"corrupt disposable stage")
    with pytest.raises(IntegrityFailure):
        jobs.stage_source(OWNER, project.project_id, job.job_id, 0)
    with pytest.raises(IntegrityFailure):
        SQLiteJobRepository(SQLiteProjectRepository(repo.files.root))


def test_stage_quota_rolls_back_metadata_leaving_reported_orphan(stage_setup):
    repo, jobs, project, job, revision = stage_setup
    repo.policy = replace(repo.policy, project_bytes=1)
    with pytest.raises(QuotaExceeded):
        jobs.append_stage(job.job_id, payload(event(revision)))
    assert not jobs.list_stages(OWNER, project.project_id, job.job_id)
    report = inventory(repo)
    assert report.unreferenced_blobs == 1 and report.unreferenced_bytes > 0 and not report.deletion_performed
    assert report.unavailable_references == 0


def test_old_v3_store_not_implicitly_upgraded(tmp_path):
    root = tmp_path / "v3"
    root.mkdir(mode=0o700)
    database = root / "metadata.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.executescript(SCHEMA_V3 + f"PRAGMA user_version=3; PRAGMA application_id={APPLICATION_ID};")
    database.chmod(0o600)
    before = database.read_bytes()
    jobs = SQLiteJobRepository(SQLiteProjectRepository(root))
    assert not jobs.supports_stages
    with pytest.raises(SchemaMismatch):
        jobs.list_stages(OWNER, "project", "job")
    assert database.read_bytes() == before


def test_inventory_bounded_missing_staging_and_no_deletion(stage_setup):
    repo, jobs, _project, job, revision = stage_setup
    receipt = jobs.append_stage(job.job_id, payload(event(revision)))
    for value in (b"orphan-1", b"orphan-2"):
        raw = RecordPayload(value, "test.v1")
        repo.files.install_blob(value, raw.content_hash)
    stage = repo.files.staging / "interrupted-test-stage"
    stage.write_bytes(b"unfinished")
    stage.chmod(0o600)
    source = repo.files.blobs / receipt.content_hash
    source.write_bytes(b"corrupt disposable source")
    before = {str(path): path.read_bytes() for path in (*repo.files.blobs.iterdir(), stage)}
    report = inventory(repo, limit=1)
    assert report.unreferenced_blobs == 2 and len(report.unreferenced_sample) == 1 and report.truncated
    assert report.staging_files == 1 and report.staging_bytes == 10
    assert report.unavailable_references == 1 and report.unavailable_sample == (receipt.content_hash,)
    assert not report.deletion_performed
    assert {str(path): path.read_bytes() for path in (*repo.files.blobs.iterdir(), stage)} == before
    assert json.loads(jobs.get(OWNER, job.project_id, job.job_id).payload)["code"] == "RUNNING"
