"""Storage/lineage contracts; synthetic payloads are not native/solver evidence."""
from __future__ import annotations

import sqlite3
from dataclasses import replace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from infrastructure.persistence.durable_jobs import SQLiteJobRepository, message
from infrastructure.persistence.inventory import inventory
from infrastructure.persistence.schema import APPLICATION_ID, SCHEMA_V4
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from simulation.contracts import StudySettings, StudySnapshot
from simulation.workbench import mesh
from systems.contracts.geometry._wire import GeometryContractError, dumps
from systems.persistence.job_repository import JobState
from systems.persistence.project_repository import Dependency, RecordPayload
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
from systems.projects.study_authority import ManagedStudies, SavedStudy, study_payload
from tests.unit_tests.simulation.test_contracts import fixture

OWNER = Principal("USR-study-storage", "ENGINEER")


def save(repo, project, domain, name, *, dependencies=(), prior=None):
    return repo.save_snapshot(OWNER, project.project_id, domain=domain, object_id=name, input_revision=0 if prior is None else prior.input_revision+1,
        payload=RecordPayload.from_mapping({"synthetic_storage_only": str(uuid4())}, "test.synthetic.v1"),
        expected=Head.absent() if prior is None else prior.head, operation_id=str(uuid4()), dependencies=dependencies)


@pytest.fixture
def setup(tmp_path):
    repo = SQLiteProjectRepository(tmp_path / "root")
    jobs = SQLiteJobRepository(repo)
    project = repo.create_project(OWNER, title="R05.4 storage test only", operation_id="project")
    geometry = save(repo, project, "geometry-fixture", "geometry")
    geometry_job = jobs.admit(OWNER, geometry, operation_id="geometry-attempt", request_hash="1"*64)
    jobs.advance(geometry_job.job_id, JobState.RUNNING, message("RUNNING"))
    jobs.advance(geometry_job.job_id, JobState.COMPLETED, message("SYNTHETIC_NOT_NATIVE"), actor=OWNER)
    dependency = Dependency("geometry", geometry.commit_id, geometry_job.job_id)
    study = save(repo, project, "simulation-benchmark", "study", dependencies=(dependency,))
    return repo, jobs, project, geometry, study


def admit(jobs, source):
    job = jobs.admit(OWNER, source, operation_id=str(uuid4()), request_hash="2"*64)
    return jobs.advance(job.job_id, JobState.RUNNING, message("RUNNING"))


def monitor(sequence=0, index=0, **changes):
    value = {"seq": sequence, "iteration": index, "normalized_residual": .1, "power_imbalance_w": -.002, "correlation_id": "sim-synthetic-storage", **changes}
    return RecordPayload.from_mapping(value, "cosmos.simulation-monitor.v1", source_namespace="p07-software-fixtures")


def test_transitive_exact_dependencies_survive_restart_and_selective_staleness(setup):
    repo, jobs, project, geometry, study = setup
    report = save(repo, project, "report-test", "report", dependencies=(Dependency("study", study.commit_id),))
    unrelated = save(repo, project, "geometry-fixture", "unrelated")
    assert repo.dependencies_current(OWNER, project.project_id, report.commit_id)
    attempt = admit(jobs, study)
    original = repo.dependencies(OWNER, project.project_id, study.commit_id)
    save(repo, project, "geometry-fixture", geometry.object_id, prior=geometry)
    assert not repo.dependencies_current(OWNER, project.project_id, study.commit_id)
    assert not repo.dependencies_current(OWNER, project.project_id, report.commit_id)
    assert repo.dependencies_current(OWNER, project.project_id, unrelated.commit_id)
    done = jobs.advance(attempt.job_id, JobState.COMPLETED, message("LATE_SOURCE"), actor=OWNER)
    assert not done.selected and not done.current_input
    with pytest.raises(InvalidRecord, match="upstream"):
        admit(jobs, study)
    reopened = SQLiteProjectRepository(repo.files.root)
    assert reopened.dependencies(OWNER, project.project_id, study.commit_id) == original
    assert reopened.get_snapshot(OWNER, project.project_id, domain=study.domain, object_id=study.object_id).payload == study.payload


def test_new_geometry_attempt_invalidates_previous_exact_job_dependency(setup):
    repo, jobs, project, geometry, study = setup
    assert repo.dependencies_current(OWNER, project.project_id, study.commit_id)
    admit(jobs, geometry)
    assert not repo.dependencies_current(OWNER, project.project_id, study.commit_id)


def test_dependency_scope_and_immutable_guards(setup):
    repo, _jobs, project, geometry, study = setup
    with pytest.raises(AccessDenied):
        repo.dependencies(Principal("USR-other", "ADMIN"), project.project_id, study.commit_id)
    foreign = repo.create_project(OWNER, title="Other project", operation_id="foreign")
    with pytest.raises(RecordNotFound):
        repo.dependencies_current(OWNER, foreign.project_id, study.commit_id)
    with pytest.raises(IntegrityFailure):
        save(repo, foreign, "simulation-benchmark", "foreign", dependencies=(Dependency("geometry", geometry.commit_id),))
    with sqlite3.connect(repo.path) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute("DELETE FROM record_dependencies")
    assert not repo.list_objects(OWNER, foreign.project_id, domain="simulation-benchmark")


def test_original_monitors_replay_recover_and_integrity(setup):
    repo, jobs, project, _geometry, study = setup
    job = admit(jobs, study)
    first, second = monitor(), monitor(1, 20)
    a = jobs.append_monitor(job.job_id, first)
    b = jobs.append_monitor(job.job_id, second)
    jobs.verify_monitors(job.job_id, (first.data, second.data))
    reopened = SQLiteJobRepository(SQLiteProjectRepository(repo.files.root))
    assert reopened.recover() == 1
    assert reopened.list_monitors(OWNER, project.project_id, job.job_id) == (a, b)
    assert reopened.monitor_source(OWNER, project.project_id, job.job_id, 1) == second.data
    assert reopened.append_monitor(job.job_id, first) == a
    with pytest.raises(InvalidRecord):
        reopened.append_monitor(job.job_id, monitor(2, 30))
    (repo.files.blobs / a.content_hash).write_bytes(b"corrupt disposable source")
    with pytest.raises(IntegrityFailure):
        SQLiteJobRepository(SQLiteProjectRepository(repo.files.root))


@pytest.mark.parametrize("change", [{"seq": 2}, {"iteration": 0}, {"correlation_id": "other"}, {"normalized_residual": -1.}, {"iteration": True}])
def test_monitor_sequence_identity_and_quantity_refusal(setup, change):
    _repo, jobs, project, _geometry, study = setup
    job = admit(jobs, study)
    jobs.append_monitor(job.job_id, monitor())
    with pytest.raises(InvalidRecord):
        jobs.append_monitor(job.job_id, monitor(1, 20, **change))
    assert len(jobs.list_monitors(OWNER, project.project_id, job.job_id)) == 1


def test_monitor_scope_quota_and_orphan_accounting(setup):
    repo, jobs, project, _geometry, study = setup
    job = admit(jobs, study)
    with pytest.raises(AccessDenied):
        jobs.list_monitors(Principal("USR-other", "ENGINEER"), project.project_id, job.job_id)
    with pytest.raises(InvalidRecord):
        jobs.list_monitors(OWNER, project.project_id, job.job_id, limit=101)
    repo.policy = replace(repo.policy, project_bytes=1)
    with pytest.raises(QuotaExceeded):
        jobs.append_monitor(job.job_id, monitor())
    assert not jobs.list_monitors(OWNER, project.project_id, job.job_id)
    report = inventory(repo)
    assert report.unreferenced_blobs == 1 and not report.unavailable_references and not report.deletion_performed


def test_exact_v4_is_readable_never_implicitly_upgraded(tmp_path):
    root = tmp_path / "v4"
    root.mkdir(mode=0o700)
    database = root / "metadata.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.executescript(SCHEMA_V4 + f"PRAGMA user_version=4; PRAGMA application_id={APPLICATION_ID};")
    database.chmod(0o600)
    before = database.read_bytes()
    repo = SQLiteProjectRepository(root)
    jobs = SQLiteJobRepository(repo)
    assert not repo.supports_dependencies and not jobs.supports_monitors
    with pytest.raises(SchemaMismatch):
        jobs.list_monitors(OWNER, "project", "run")
    assert database.read_bytes() == before


def test_saved_changed_method_identity_refused_before_admission_or_materialization(setup):
    repo, jobs, project, geometry, study_source = setup
    dependency = repo.dependencies(OWNER, project.project_id, study_source.commit_id)[0]
    # Synthetic contract fixture only: proves refusal, never a native/solver success.
    study = replace(StudySnapshot(fixture(), StudySettings()), solver_sha256="0"*64)
    saved = SavedStudy(study, dumps(mesh(study)), geometry.commit_id, dependency.job_id)
    source = repo.save_snapshot(OWNER, project.project_id, domain="simulation-benchmark", object_id="old-methods", input_revision=0,
        payload=study_payload(saved), expected=Head.absent(), operation_id="old-method-input", dependencies=(dependency,))
    materializer = Mock(side_effect=AssertionError("Stale methods must be refused before execution scratch exists"))
    coordinator = ManagedStudies(repo, jobs, materializer, lambda _user: OWNER)
    try:
        with pytest.raises(GeometryContractError) as error:
            coordinator.start(OWNER, source, operation_id="should-not-admit", request_hash="7"*64)
        assert error.value.code == "SOURCE_CHANGED"
        materializer.assert_not_called()
        assert not jobs.list_ids(OWNER, project.project_id, object_id="old-methods", domain="simulation-benchmark")
    finally:
        coordinator.close()


def test_corrupt_upstream_bytes_are_not_current_but_own_history_is_preserved(setup):
    repo, jobs, project, geometry, study = setup
    job = admit(jobs, study)
    (repo.files.blobs / geometry.head.content_hash).write_bytes(b"corrupt disposable upstream input")
    assert not repo.dependencies_current(OWNER, project.project_id, study.commit_id)
    done = jobs.advance(job.job_id, JobState.COMPLETED, message("LATE_AFTER_CORRUPTION"), actor=OWNER)
    assert not done.selected and not done.current_input
    assert repo.get_snapshot(OWNER, project.project_id, domain=study.domain, object_id=study.object_id).payload == study.payload


def test_trusted_method_selection_gate_retains_completed_history_without_selecting(setup):
    _repo, jobs, project, _geometry, study = setup
    job = admit(jobs, study)
    with pytest.raises(InvalidRecord):
        jobs.advance(job.job_id, JobState.COMPLETED, message("BAD_GATE"), actor=OWNER, selection_allowed="yes")
    done = jobs.advance(job.job_id, JobState.COMPLETED, message("METHOD_CHANGED"), actor=OWNER, selection_allowed=False)
    assert done.state is JobState.COMPLETED and not done.selected
    assert jobs.get(OWNER, project.project_id, job.job_id).payload == done.payload


def test_domain_scoped_job_paging_never_mixes_equal_object_ids(setup):
    repo, jobs, project, _geometry, _study = setup
    geometry = save(repo, project, "geometry-fixture", "shared")
    study = save(repo, project, "simulation-benchmark", "shared")
    a, b = admit(jobs, geometry), admit(jobs, study)
    assert [value[1] for value in jobs.list_ids(OWNER, project.project_id, object_id="shared", domain="geometry-fixture")] == [a.job_id]
    assert [value[1] for value in jobs.list_ids(OWNER, project.project_id, object_id="shared", domain="simulation-benchmark")] == [b.job_id]
