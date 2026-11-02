"""R05.3 temporary authority: attempts, exact bytes, CAS, and recovery."""
from __future__ import annotations

import errno
import sqlite3
from hashlib import sha256
from uuid import uuid4

import pytest

from infrastructure.persistence import files as file_io
from infrastructure.persistence.application_authority import ApplicationAuthority
from infrastructure.persistence.durable_jobs import SQLiteJobRepository, message
from infrastructure.persistence.inventory import inventory
from infrastructure.persistence.schema import APPLICATION_ID, SCHEMA_V2
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.persistence.job_repository import BlobAttachment, JobState
from systems.persistence.project_repository import RecordPayload
from systems.projects.authority import (
    AccessDenied,
    Head,
    HeadConflict,
    IntegrityFailure,
    InvalidRecord,
    Lifecycle,
    OperationConflict,
    Principal,
    QuotaExceeded,
    RecordNotFound,
    SchemaMismatch,
    StoreUnavailable,
)

OWNER = Principal("USR-owner", "ENGINEER")
OTHER = Principal("USR-other", "ENGINEER")
HASH = sha256(b"request").hexdigest()


@pytest.fixture
def setup(tmp_path):
    repo = SQLiteProjectRepository(tmp_path / "root")
    jobs = SQLiteJobRepository(repo)
    project = repo.create_project(OWNER, title="Synthetic attempt tests", mission="Software only", operation_id="project")
    source = repo.save_snapshot(OWNER, project.project_id, domain="geometry-fixture", object_id="fixture-1", input_revision=0,
        payload=RecordPayload(b'{"source":"exact"}', "test.input.v1", "p07-software-fixtures"), expected=Head.absent(), operation_id="input")
    return repo, jobs, project, source


def admit(jobs, source, **extra):
    return jobs.admit(OWNER, source, operation_id=str(uuid4()), request_hash=HASH, **extra)


def complete(jobs, job, data=b"exact synthetic artifact"):
    jobs.advance(job.job_id, JobState.RUNNING, message("RUNNING"))
    return jobs.advance(job.job_id, JobState.COMPLETED, message("SOFTWARE_ONLY"), actor=OWNER,
        attachments=(BlobAttachment("export.step", data, sha256(data).hexdigest(), "artifact"),))


def test_exact_bytes_and_terminal_events_survive_restart(setup):
    repo, jobs, project, source = setup
    job = admit(jobs, source)
    done = complete(jobs, job)
    assert done.selected and done.current_input
    reopened = SQLiteJobRepository(SQLiteProjectRepository(repo.files.root))
    assert reopened.get(OWNER, project.project_id, job.job_id) == done
    assert reopened.blob(OWNER, project.project_id, job.job_id, "export.step") == b"exact synthetic artifact"
    assert reopened.recover() == 0
    with pytest.raises(InvalidRecord, match="Terminal"):
        reopened.advance(job.job_id, JobState.FAILED, message("REWRITE"))


def test_retry_operation_collision_and_exact_receipt(setup):
    _repo, jobs, _project, source = setup
    original = jobs.admit(OWNER, source, operation_id="start", request_hash=HASH)
    complete(jobs, original)
    replay = jobs.admit(OWNER, source, operation_id="start", request_hash=HASH)
    assert replay.state is JobState.QUEUED and replay.payload == original.payload
    assert replay.job_id == original.job_id
    with pytest.raises(OperationConflict):
        jobs.admit(OWNER, source, operation_id="start", request_hash="0"*64)
    retried = admit(jobs, source, retry_of=original.job_id)
    assert retried.retry_of == original.job_id and retried.job_id != original.job_id
    assert not jobs.get(OWNER, source.project_id, original.job_id).selected


def test_stale_input_and_superseded_attempt_never_selected(setup):
    repo, jobs, project, source = setup
    first = admit(jobs, source)
    newer_attempt = admit(jobs, source)
    assert not complete(jobs, first).selected
    assert complete(jobs, newer_attempt).selected
    newer_input = repo.save_snapshot(OWNER, project.project_id, domain=source.domain, object_id=source.object_id,
        input_revision=1, payload=RecordPayload(b'{"source":"changed"}', "test.input.v1"), expected=source.head, operation_id="edit")
    assert not jobs.get(OWNER, project.project_id, newer_attempt.job_id).current_input
    with pytest.raises(HeadConflict):
        admit(jobs, source)
    late = admit(jobs, newer_input)
    repo.save_snapshot(OWNER, project.project_id, domain=source.domain, object_id=source.object_id,
        input_revision=2, payload=RecordPayload(b'{"source":"again"}', "test.input.v1"), expected=newer_input.head, operation_id="edit2")
    assert not complete(jobs, late).selected


def test_cancel_compare_token_and_late_accepted_bytes_cannot_publish(setup):
    _repo, jobs, project, source = setup
    job = admit(jobs, source)
    running = jobs.advance(job.job_id, JobState.RUNNING, message("RUNNING"))
    with pytest.raises(HeadConflict):
        jobs.cancel(OWNER, project.project_id, job.job_id, expected=job.head, operation_id="cancel-old", request_hash=HASH)
    requested = jobs.cancel(OWNER, project.project_id, job.job_id, expected=running.head, operation_id="cancel", request_hash=HASH)
    assert requested.state is JobState.CANCEL_REQUESTED
    done = jobs.advance(job.job_id, JobState.COMPLETED, message("LATE_RESULT"), actor=OWNER,
        attachments=(BlobAttachment("export.step", b"late", sha256(b"late").hexdigest(), "artifact"),))
    assert done.state is JobState.CANCELLED and not done.blobs and not done.selected
    assert jobs.cancel(OWNER, project.project_id, job.job_id, expected=running.head, operation_id="cancel", request_hash=HASH).state is JobState.CANCEL_REQUESTED


@pytest.mark.parametrize("state", [JobState.QUEUED, JobState.RUNNING, JobState.CANCEL_REQUESTED])
def test_recovery_interrupts_only_nonterminal_without_auto_retry(setup, state):
    _repo, jobs, project, source = setup
    completed = complete(jobs, admit(jobs, source))
    job = admit(jobs, source)
    if state is not JobState.QUEUED:
        job = jobs.advance(job.job_id, JobState.RUNNING, message("RUNNING"))
    if state is JobState.CANCEL_REQUESTED:
        jobs.cancel(OWNER, project.project_id, job.job_id, expected=job.head, operation_id="cancel", request_hash=HASH)
    assert jobs.recover() == 1 and jobs.recover() == 0
    assert jobs.get(OWNER, project.project_id, job.job_id).state is JobState.INTERRUPTED
    assert jobs.get(OWNER, project.project_id, completed.job_id).events == completed.events


def test_cross_actor_project_and_archive_fail_closed(setup):
    repo, jobs, project, source = setup
    job = admit(jobs, source)
    with pytest.raises(AccessDenied):
        jobs.get(OTHER, project.project_id, job.job_id)
    foreign = repo.create_project(OWNER, title="Other scope", mission="Test", operation_id="other-project")
    with pytest.raises(RecordNotFound):
        jobs.get(OWNER, foreign.project_id, job.job_id)
    with pytest.raises(AccessDenied):
        jobs.list_ids(OTHER, project.project_id, object_id=source.object_id)
    repo.change_project(OWNER, project.project_id, expected=project.head, operation_id="archive", lifecycle=Lifecycle.ARCHIVED)
    assert not complete(jobs, job).selected
    with pytest.raises(AccessDenied):
        admit(jobs, source)


def test_immutable_guards_and_metadata_before_byte_publication(setup, monkeypatch):
    repo, jobs, project, source = setup
    job = admit(jobs, source)
    jobs.advance(job.job_id, JobState.RUNNING, message("RUNNING"))
    install = repo.files.install_blob
    def fail(data, digest):
        if data == b"missing":
            raise OSError("synthetic disk failure")
        install(data, digest)
    monkeypatch.setattr(repo.files, "install_blob", fail)
    with pytest.raises(StoreUnavailable):
        jobs.advance(job.job_id, JobState.COMPLETED, message("DONE"), actor=OWNER,
            attachments=(BlobAttachment("export.step", b"missing", sha256(b"missing").hexdigest(), "artifact"),))
    assert jobs.get(OWNER, project.project_id, job.job_id).state is JobState.RUNNING
    with sqlite3.connect(repo.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM durable_job_blobs").fetchone()[0] == 0
        for table in ("durable_jobs", "durable_job_events"):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(f"DELETE FROM {table}")


def test_corruption_unavailable_and_old_schema_not_upgraded(setup, tmp_path):
    repo, jobs, project, source = setup
    done = complete(jobs, admit(jobs, source))
    path = repo.files.blobs / done.blobs[0].content_hash
    path.write_bytes(b"corrupt test fixture")
    with pytest.raises(IntegrityFailure):
        jobs.blob(OWNER, project.project_id, done.job_id, done.blobs[0].name)
    with pytest.raises(IntegrityFailure):
        SQLiteJobRepository(SQLiteProjectRepository(repo.files.root))
    # New empty independent file avoids changing or downgrading any existing store.
    pristine = tmp_path / "pristine-v2"
    pristine.mkdir(mode=0o700)
    database = pristine / "metadata.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.executescript(SCHEMA_V2 + f"PRAGMA user_version=2; PRAGMA application_id={APPLICATION_ID};")
    database.chmod(0o600)
    before = database.read_bytes()
    old_repo = SQLiteProjectRepository(pristine)
    assert old_repo.schema_version == 2 and database.read_bytes() == before
    with pytest.raises(SchemaMismatch):
        SQLiteJobRepository(old_repo).recover()
    assert database.is_file()


def test_application_holds_lease_before_recovery(tmp_path):
    app = ApplicationAuthority(tmp_path / "app", enabled=True)
    project = app.repository.create_project(OWNER, title="Restart fixture", mission="Test", operation_id="project")
    source = app.repository.save_snapshot(OWNER, project.project_id, domain="geometry-fixture", object_id="fixture", input_revision=0,
        payload=RecordPayload(b'{"test":true}', "test.record.v1"), expected=Head.absent(), operation_id="input")
    job = admit(app.jobs, source)
    with pytest.raises(StoreUnavailable):
        ApplicationAuthority(tmp_path / "app", enabled=True)
    app.close()
    restarted = ApplicationAuthority(tmp_path / "app", enabled=True)
    try:
        assert restarted.recovered_jobs == 1
        assert restarted.jobs.get(OWNER, project.project_id, job.job_id).state is JobState.INTERRUPTED
    finally:
        restarted.close()


@pytest.mark.parametrize("boundary", ["file-sync", "link", "directory-sync", "metadata-budget"])
def test_attachment_failure_boundaries_never_select_partial_outputs(setup, monkeypatch, boundary):
    repo, jobs, project, source = setup
    job = admit(jobs, source)
    jobs.advance(job.job_id, JobState.RUNNING, message("RUNNING"))
    def full(*_args, **_kwargs):
        raise OSError(errno.ENOSPC, "injected disk full")
    def quota(*_args, **_kwargs):
        raise QuotaExceeded("injected project metadata quota")
    with monkeypatch.context() as scoped:
        if boundary == "file-sync":
            scoped.setattr(file_io.os, "fsync", full)
        elif boundary == "link":
            scoped.setattr(file_io.os, "link", full)
        elif boundary == "directory-sync":
            scoped.setattr(file_io, "sync_directory", full)
        else:
            scoped.setattr(repo, "_check_project_budget", quota)
        data = b"synthetic boundary attachment"
        with pytest.raises(QuotaExceeded):
            jobs.advance(job.job_id, JobState.COMPLETED, message("DONE"), actor=OWNER,
                attachments=(BlobAttachment("export.step", data, sha256(data).hexdigest(), "artifact"),))
    retained = jobs.get(OWNER, project.project_id, job.job_id)
    assert retained.state is JobState.RUNNING and not retained.selected and not retained.blobs
    report = inventory(repo)
    assert not report.deletion_performed and report.unavailable_references == 0
    assert report.staging_files or report.unreferenced_blobs
    reopened = SQLiteJobRepository(SQLiteProjectRepository(repo.files.root))
    assert reopened.recover() == 1 and reopened.get(OWNER, project.project_id, job.job_id).state is JobState.INTERRUPTED


@pytest.mark.parametrize("actor", [Principal(OWNER.user_id, "VIEWER"), Principal(OWNER.user_id, "ENGINEER", False), OTHER])
def test_late_completion_with_changed_identity_or_role_is_not_selected(setup, actor):
    _repo, jobs, project, source = setup
    job = admit(jobs, source)
    jobs.advance(job.job_id, JobState.RUNNING, message("RUNNING"))
    done = jobs.advance(job.job_id, JobState.COMPLETED, message("SOFTWARE_ONLY"), actor=actor)
    assert done.state is JobState.COMPLETED and not done.selected
    assert not jobs.get(OWNER, project.project_id, job.job_id).selected
