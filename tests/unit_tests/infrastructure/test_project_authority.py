"""R05.1 evidence in isolated storage; never the user's application data."""

from __future__ import annotations

import errno
import json
import os
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier, Event

import pytest

import infrastructure.persistence.files as file_io
from core.quantity import Quantity
from core.serialization import canonical_json_dumps
from core.unit import SI
from infrastructure.persistence.files import CoordinatorLease
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.persistence.project_repository import ProjectRepository, RecordPayload
from systems.projects.authority import (
    AccessDenied,
    Head,
    HeadConflict,
    IntegrityFailure,
    InvalidRecord,
    Lifecycle,
    Membership,
    OperationConflict,
    Principal,
    Project,
    QuotaExceeded,
    RecordNotFound,
    SchemaMismatch,
    StoragePolicy,
    StoreUnavailable,
)
from systems.projects.models import PropulsionDesign

OWNER = Principal("USR-owner", "ENGINEER")
OTHER = Principal("USR-other", "ENGINEER")
PAYLOAD = RecordPayload(
    b'{"value":0,"unit":"Pa"}', "test.record.v1", "p07-software-fixtures"
)


@pytest.fixture
def store(tmp_path: Path) -> SQLiteProjectRepository:
    return SQLiteProjectRepository(tmp_path / "engineering_state" / "v1")


@pytest.fixture
def project(store: SQLiteProjectRepository) -> Project:
    return store.create_project(
        OWNER,
        title="Synthetic project — not hardware evidence",
        mission="R05 tests",
        operation_id="create",
    )


def _save(store: SQLiteProjectRepository, project_id: str, **changes):
    kwargs = {
        "domain": "propulsion",
        "object_id": "design-1",
        "input_revision": 17,
        "payload": PAYLOAD,
        "expected": Head.absent(),
        "operation_id": "save",
    }
    kwargs.update(changes)
    return store.save_snapshot(OWNER, project_id, **kwargs)


def _counts(store: SQLiteProjectRepository) -> tuple[int, ...]:
    with sqlite3.connect(store.path) as connection:
        return tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "projects",
                "objects",
                "commits",
                "project_events",
                "operations",
            )
        )


def test_protocol_create_reopen_and_canonical_propulsion(store, project):
    typed: ProjectRepository = store
    assert typed.get_project(OWNER, project.project_id) == project
    design = PropulsionDesign(
        name="Immutable source", engineer="descriptive, not authority"
    )
    design.requirements.target_thrust = Quantity(0.0, SI.get("N"))
    payload = RecordPayload.from_design(design)
    saved = _save(
        store,
        project.project_id,
        payload=payload,
        object_id=design.design_id,
        input_revision=design.revision,
    )
    design.name = "Unpersisted edit"
    restarted = SQLiteProjectRepository(store.files.root)
    loaded = restarted.get_snapshot(
        OWNER, project.project_id, domain="propulsion", object_id=design.design_id
    )
    assert loaded == saved
    restored = PropulsionDesign.from_canonical_dict(json.loads(loaded.payload))
    assert restored.name == "Immutable source"
    assert restored.requirements.target_thrust.to_si() == 0
    assert loaded.creator_user_id == OWNER.user_id
    assert loaded.payload == payload.data
    assert loaded.payload == canonical_json_dumps(json.loads(payload.data)).encode()


def test_same_input_revision_recalculation_retains_distinct_immutable_commits(
    store, project
):
    first = _save(store, project.project_id)
    second = _save(
        store, project.project_id, expected=first.head, operation_id="calculate-again"
    )
    assert first.input_revision == second.input_revision == 17
    assert first.head.content_hash == second.head.content_hash
    assert (first.head.version, second.head.version) == (1, 2)
    assert first.commit_id != second.commit_id
    assert second.parent_commit_id == first.commit_id
    assert (
        store.get_snapshot(
            OWNER,
            project.project_id,
            domain="propulsion",
            object_id="design-1",
            commit_id=first.commit_id,
        )
        == first
    )
    assert store.list_commit_ids(
        OWNER, project.project_id, domain="propulsion", object_id="design-1", limit=1
    ) == (second.commit_id,)
    assert store.list_commit_ids(
        OWNER,
        project.project_id,
        domain="propulsion",
        object_id="design-1",
        before_version=2,
    ) == (first.commit_id,)


def test_source_number_spelling_units_and_namespace_are_not_rewritten(store, project):
    raw = b'{ "project_id":"p07-software-fixtures", "value":1.234567890123456789, "zero":-0.0, "unit":"m/s" }\n'
    saved = _save(
        store,
        project.project_id,
        payload=RecordPayload(raw, "test.record.v1", "p07-software-fixtures"),
    )
    assert saved.payload == raw
    assert saved.source_namespace == "p07-software-fixtures"
    assert saved.project_id == project.project_id != saved.source_namespace


def test_expected_version_and_hash_are_both_required(store, project):
    first = _save(store, project.project_id)
    for expected in (
        Head(0, first.head.content_hash),
        Head(1, Head.absent().content_hash),
    ):
        with pytest.raises(HeadConflict) as caught:
            _save(store, project.project_id, expected=expected, operation_id="stale")
        assert caught.value.current == first.head
    assert _counts(store)[2] == 1


def test_operations_are_idempotent_and_content_collisions_refused(store, project):
    assert (
        store.create_project(
            OWNER, title=project.title, mission=project.mission, operation_id="create"
        )
        == project
    )
    first = _save(store, project.project_id)
    assert _save(store, project.project_id) == first
    with pytest.raises(OperationConflict):
        _save(
            store,
            project.project_id,
            payload=RecordPayload(b'{"value":1}', "test.record.v1"),
        )
    with pytest.raises(OperationConflict):
        store.create_project(OWNER, title="Different", operation_id="create")
    assert _counts(store) == (1, 1, 1, 2, 2)


@pytest.mark.parametrize("role", ["VIEWER", "REVIEWER", "APPROVER", "UNKNOWN"])
def test_global_role_intersection_never_grants_engineering_writes(store, project, role):
    member = Principal("USR-member", role)
    if role != "UNKNOWN":
        store.set_member(
            OWNER,
            project.project_id,
            member=member,
            capability=Membership.EDITOR,
            expected=project.head,
            operation_id="grant",
        )
    with pytest.raises(AccessDenied):
        store.create_project(member, title="Denied", operation_id="forbidden-create")
    with pytest.raises(AccessDenied):
        store.save_snapshot(
            member,
            project.project_id,
            domain="propulsion",
            object_id="design-1",
            input_revision=0,
            payload=PAYLOAD,
            expected=Head.absent(),
            operation_id="forbidden-save",
        )


def test_membership_owner_and_global_admin_are_not_cross_project_authority(
    store, project
):
    saved = _save(store, project.project_id)
    for outsider in (OTHER, Principal("USR-admin", "ADMIN")):
        with pytest.raises(AccessDenied):
            store.get_snapshot(
                outsider,
                project.project_id,
                domain="propulsion",
                object_id="design-1",
                commit_id=saved.commit_id,
            )
        assert store.list_projects(outsider) == ()
    viewer = Principal("USR-viewer", "ENGINEER")
    updated = store.set_member(
        OWNER,
        project.project_id,
        member=viewer,
        capability=Membership.VIEWER,
        expected=project.head,
        operation_id="grant-view",
    )
    assert (
        store.get_snapshot(
            viewer, project.project_id, domain="propulsion", object_id="design-1"
        )
        == saved
    )
    with pytest.raises(AccessDenied):
        store.change_project(
            viewer,
            project.project_id,
            expected=updated.head,
            title="Bad",
            operation_id="rename",
        )
    with pytest.raises(AccessDenied):
        store.set_member(
            viewer,
            project.project_id,
            member=OTHER,
            capability=Membership.EDITOR,
            expected=updated.head,
            operation_id="grant-others",
        )
    with pytest.raises(AccessDenied):
        store.set_member(
            OWNER,
            project.project_id,
            member=OWNER,
            capability=None,
            expected=updated.head,
            operation_id="remove-owner",
        )
    with pytest.raises(AccessDenied):
        store.get_project(replace(OWNER, active=False), project.project_id)
    removed = store.set_member(
        OWNER,
        project.project_id,
        member=viewer,
        capability=None,
        expected=updated.head,
        operation_id="remove-viewer",
    )
    assert removed.head.version == 3
    with pytest.raises(AccessDenied):
        store.get_project(viewer, project.project_id)


def test_editor_writes_but_cannot_change_lifecycle(store, project):
    updated = store.set_member(
        OWNER,
        project.project_id,
        member=OTHER,
        capability=Membership.EDITOR,
        expected=project.head,
        operation_id="grant-edit",
    )
    renamed = store.change_project(
        OTHER,
        project.project_id,
        expected=updated.head,
        title="Editor rename",
        operation_id="edit",
    )
    assert renamed.title == "Editor rename"
    with pytest.raises(AccessDenied):
        store.change_project(
            OTHER,
            project.project_id,
            expected=renamed.head,
            lifecycle=Lifecycle.ARCHIVED,
            operation_id="archive",
        )


def test_archive_tombstone_restore_retain_sources_and_require_confirmation(
    store, project
):
    saved = _save(store, project.project_id)
    archived = store.change_project(
        OWNER,
        project.project_id,
        expected=project.head,
        lifecycle=Lifecycle.ARCHIVED,
        operation_id="archive",
    )
    with pytest.raises(AccessDenied):
        _save(
            store, project.project_id, expected=saved.head, operation_id="after-archive"
        )
    with pytest.raises(AccessDenied):
        store.change_project(
            OWNER,
            project.project_id,
            expected=archived.head,
            title="Not allowed",
            operation_id="archived-edit",
        )
    with pytest.raises(InvalidRecord):
        store.change_project(
            OWNER,
            project.project_id,
            expected=archived.head,
            lifecycle=Lifecycle.DELETED,
            operation_id="delete",
        )
    deleted = store.change_project(
        OWNER,
        project.project_id,
        expected=archived.head,
        lifecycle=Lifecycle.DELETED,
        confirmation_project_id=project.project_id,
        operation_id="delete",
    )
    assert deleted.lifecycle is Lifecycle.DELETED
    assert (
        store.get_snapshot(
            OWNER, project.project_id, domain="propulsion", object_id="design-1"
        )
        == saved
    )
    restored = store.change_project(
        OWNER,
        project.project_id,
        expected=deleted.head,
        lifecycle=Lifecycle.ACTIVE,
        operation_id="restore",
    )
    assert restored.lifecycle is Lifecycle.ACTIVE
    assert (
        _save(
            store, project.project_id, expected=saved.head, operation_id="after-restore"
        ).head.version
        == 2
    )


def test_equal_hash_in_other_project_does_not_authorize_commit_substitution(
    store, project
):
    first = _save(store, project.project_id)
    other = store.create_project(OTHER, title="Other owner", operation_id="create")
    second = store.save_snapshot(
        OTHER,
        other.project_id,
        domain="propulsion",
        object_id="design-1",
        input_revision=17,
        payload=PAYLOAD,
        expected=Head.absent(),
        operation_id="save",
    )
    assert first.head.content_hash == second.head.content_hash
    assert len(list(store.files.blobs.iterdir())) == 1
    with pytest.raises(RecordNotFound):
        store.get_snapshot(
            OTHER,
            other.project_id,
            domain="propulsion",
            object_id="design-1",
            commit_id=first.commit_id,
        )


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":1e9999}',
        b'{"x":1,"x":2}',
        b"[]",
        b"\xff",
        b"{",
        b'{"x":' + b"[" * 1100 + b"0" + b"]" * 1100 + b"}",
    ],
)
def test_invalid_nonfinite_ambiguous_or_unbounded_sources_are_refused(
    store, project, raw
):
    with pytest.raises(InvalidRecord):
        _save(store, project.project_id, payload=RecordPayload(raw, "test.record.v1"))
    assert _counts(store)[2] == 0
    assert not list(store.files.blobs.iterdir())


@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), {1: "invalid"}, object(), 1 << 257]
)
def test_mapping_factory_refuses_invalid_values(value):
    with pytest.raises(InvalidRecord):
        RecordPayload.from_mapping({"value": value}, "test.record.v1")


@pytest.mark.parametrize("bad", ["../escape", "/absolute", "a/b", "", "x" * 129])
def test_path_like_object_ids_refused(store, project, bad):
    with pytest.raises(InvalidRecord):
        _save(store, project.project_id, object_id=bad)


def test_transaction_failure_keeps_orphan_but_never_partial_metadata(
    store, project, monkeypatch
):
    before = _counts(store)
    event = store._event

    def fail(*args, **kwargs):
        raise RuntimeError("Injected failure after blob and SQL insert")

    monkeypatch.setattr(store, "_event", fail)
    with pytest.raises(RuntimeError):
        _save(store, project.project_id)
    assert _counts(store) == before
    assert (
        store.files.read_blob(PAYLOAD.content_hash, len(PAYLOAD.data)) == PAYLOAD.data
    )
    monkeypatch.setattr(store, "_event", event)
    assert _save(store, project.project_id).head.version == 1


def test_corrupt_source_and_missing_source_fail_closed(store, project):
    _save(store, project.project_id)
    path = store.files.blobs / PAYLOAD.content_hash
    original = path.read_bytes()
    # Deliberate test corruption, not a production record editing path.
    with path.open("wb") as stream:
        stream.write(b"x" * len(original))
    with pytest.raises(IntegrityFailure):
        store.get_snapshot(
            OWNER, project.project_id, domain="propulsion", object_id="design-1"
        )
    with pytest.raises(IntegrityFailure):
        SQLiteProjectRepository(store.files.root)
    path.unlink()
    with pytest.raises(IntegrityFailure):
        SQLiteProjectRepository(store.files.root)


@pytest.mark.parametrize(
    "sql",
    [
        "PRAGMA user_version=99",
        "DROP TRIGGER immutable_commits_update",
        "ALTER TABLE commits ADD COLUMN surprise TEXT",
    ],
)
def test_unknown_or_modified_schema_is_not_repaired(store, sql):
    with sqlite3.connect(store.path) as connection:
        connection.execute(sql)
    before = store.path.read_bytes()
    with pytest.raises(SchemaMismatch):
        SQLiteProjectRepository(store.files.root)
    assert store.path.read_bytes() == before


@pytest.mark.parametrize(
    "table", ["commits", "project_events", "operations", "store_format"]
)
def test_immutable_tables_reject_update_and_delete(store, project, table):
    _save(store, project.project_id)
    with sqlite3.connect(store.path) as connection:
        column = connection.execute(f"PRAGMA table_info({table})").fetchone()[1]
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(f"UPDATE {table} SET {column}={column}")
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(f"DELETE FROM {table}")


def test_private_root_file_symlink_and_hardlink_refusal(tmp_path):
    real = tmp_path / "real"
    real.mkdir(mode=0o700)
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(IntegrityFailure):
        SQLiteProjectRepository(alias / "nested")
    unsafe = tmp_path / "unsafe"
    unsafe.mkdir(mode=0o755)
    with pytest.raises(IntegrityFailure):
        SQLiteProjectRepository(unsafe)
    repo = SQLiteProjectRepository(tmp_path / "safe")
    db_alias = tmp_path / "database-alias"
    os.link(repo.path, db_alias)
    with pytest.raises(IntegrityFailure):
        SQLiteProjectRepository(repo.files.root)


def test_blob_symlink_does_not_overwrite_external_file(store, project, tmp_path):
    target = tmp_path / "external"
    target.write_bytes(b"must survive")
    (store.files.blobs / PAYLOAD.content_hash).symlink_to(target)
    with pytest.raises(IntegrityFailure):
        _save(store, project.project_id)
    assert target.read_bytes() == b"must survive"
    assert _counts(store)[2] == 0


def test_root_budget_counts_staging_and_orphan_bytes_without_eviction(store, project):
    occupied = store.files.staging / "interrupted"
    occupied.write_bytes(b"unreferenced bytes must remain")
    bounded = SQLiteProjectRepository(
        store.files.root,
        policy=replace(store.policy, store_bytes=store.files.usage_bytes() + 10),
    )
    with pytest.raises(QuotaExceeded):
        _save(bounded, project.project_id)
    assert occupied.read_bytes() == b"unreferenced bytes must remain"
    assert _counts(store)[2] == 0


def test_record_and_project_budgets_preserve_history(store, project):
    bounded = SQLiteProjectRepository(
        store.files.root, policy=replace(store.policy, record_bytes=8)
    )
    with pytest.raises(InvalidRecord):
        _save(bounded, project.project_id)
    first = _save(store, project.project_id)
    bounded = SQLiteProjectRepository(
        store.files.root, policy=replace(store.policy, project_bytes=len(PAYLOAD.data))
    )
    with pytest.raises(QuotaExceeded):
        _save(bounded, project.project_id, expected=first.head, operation_id="second")
    assert (
        store.get_snapshot(
            OWNER, project.project_id, domain="propulsion", object_id="design-1"
        )
        == first
    )


def test_coordinator_lease_excludes_second_live_coordinator_and_releases(store):
    with (
        CoordinatorLease(store.files.root),
        pytest.raises(StoreUnavailable, match="Another coordinator"),
    ):
        CoordinatorLease(store.files.root)
    with CoordinatorLease(store.files.root):
        assert store.path.exists()


def test_short_transaction_lock_timeout_is_typed(store, project):
    short = SQLiteProjectRepository(
        store.files.root, policy=replace(store.policy, busy_timeout_ms=30)
    )
    with store.files.write_lock(), pytest.raises(StoreUnavailable, match="busy"):
        _save(short, project.project_id)


def test_read_waits_for_writer_journal_removal_before_private_file_check(
    store, project, monkeypatch
):
    saved = _save(store, project.project_id)
    sidecar = store.path.with_name(store.path.name + "-journal")
    entered, opened, removed = Event(), Event(), Event()
    original_open = file_io.os.open

    def observe_open(path, flags, *args, **kwargs):
        fd = original_open(path, flags, *args, **kwargs)
        if Path(path) == sidecar:
            opened.set()
            assert removed.wait(2)
        return fd

    def reader():
        entered.set()
        return store.get_snapshot(
            OWNER, project.project_id, domain="propulsion", object_id="design-1"
        )

    monkeypatch.setattr(file_io.os, "open", observe_open)
    with ThreadPoolExecutor(max_workers=1) as pool:
        with store.files.write_lock():
            fd = original_open(sidecar, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            os.close(fd)
            future = pool.submit(reader)
            assert entered.wait(2)
            # Reproduce the legitimate unlink-between-open-and-fstat window if
            # the reader bypasses the cooperative IO lock. With that lock it
            # cannot inspect the transient sidecar at all.
            opened.wait(0.15)
            sidecar.unlink()
            removed.set()
        assert future.result(timeout=3) == saved


def test_threads_and_separate_handles_produce_exactly_one_winner(store, project):
    barrier = Barrier(2)
    handles = [
        SQLiteProjectRepository(store.files.root),
        SQLiteProjectRepository(store.files.root),
    ]

    def writer(index):
        barrier.wait(timeout=5)
        try:
            _save(handles[index], project.project_id, operation_id=f"thread-{index}")
            return "saved"
        except HeadConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(writer, (0, 1)))
    assert sorted(outcomes) == ["conflict", "saved"]
    assert _counts(store)[2] == 1


_PROCESS_SAVE = r"""
import json, os, signal, sys
from contextlib import contextmanager
from pathlib import Path
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.persistence.project_repository import RecordPayload
from systems.projects.authority import Principal, Head, HeadConflict
config=json.loads(sys.argv[1])
store=SQLiteProjectRepository(Path(config['root']))
if config.get('crash') == 'sql':
    store._event=lambda *args, **kwargs: os.kill(os.getpid(), signal.SIGKILL)
elif config.get('crash') == 'blob':
    import infrastructure.persistence.files as files
    files.sync_directory=lambda *args: os.kill(os.getpid(), signal.SIGKILL)
elif config.get('crash') == 'ack':
    original=store._transaction
    @contextmanager
    def crash_after_commit(**kwargs):
        with original(**kwargs) as connection:
            yield connection
        os.kill(os.getpid(), signal.SIGKILL)
    store._transaction=crash_after_commit
print('ready', flush=True)
sys.stdin.readline()
try:
    saved=store.save_snapshot(Principal('USR-owner','ENGINEER'),config['project'],domain='propulsion',object_id='design-1',input_revision=17,payload=RecordPayload(b'{"value":0,"unit":"Pa"}', 'test.record.v1','p07-software-fixtures'),expected=Head.absent(),operation_id=config['operation'])
    print(json.dumps({'status':'saved','commit':saved.commit_id}),flush=True)
except HeadConflict:
    print(json.dumps({'status':'conflict'}),flush=True)
"""


def _child(store, project, operation, crash=None):
    config = {
        "root": str(store.files.root),
        "project": project.project_id,
        "operation": operation,
        "crash": crash,
    }
    child = subprocess.Popen(
        [sys.executable, "-c", _PROCESS_SAVE, json.dumps(config)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert child.stdout.readline().strip() == "ready"
    return child


def test_separate_process_cas_one_commit_one_conflict(store, project):
    children = [_child(store, project, f"process-{index}") for index in range(2)]
    try:
        for child in children:
            child.stdin.write("go\n")
            child.stdin.flush()
        outcomes = []
        for child in children:
            output, error = child.communicate(timeout=15)
            assert child.returncode == 0, error
            outcomes.append(json.loads(output)["status"])
        assert sorted(outcomes) == ["conflict", "saved"]
        assert _counts(store)[2] == 1
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)


@pytest.mark.parametrize("boundary", ["blob", "sql", "ack"])
def test_sigkill_recovery_never_publishes_partial_and_retry_is_idempotent(
    store, project, boundary
):
    child = _child(store, project, "crash-save", boundary)
    child.communicate("go\n", timeout=15)
    assert child.returncode == -9
    restarted = SQLiteProjectRepository(store.files.root)
    committed = _counts(restarted)[2]
    assert committed == (1 if boundary == "ack" else 0)
    if boundary != "ack":
        with pytest.raises(RecordNotFound):
            restarted.get_snapshot(
                OWNER, project.project_id, domain="propulsion", object_id="design-1"
            )
    saved = _save(restarted, project.project_id, operation_id="crash-save")
    assert _counts(restarted)[2] == 1
    assert saved.payload == PAYLOAD.data
    assert _save(restarted, project.project_id, operation_id="crash-save") == saved


@pytest.mark.parametrize("version", [-1, True, 2**63, 1.2])
def test_head_rejects_invalid_versions(version):
    with pytest.raises(InvalidRecord):
        Head(version, "a" * 64)


@pytest.mark.parametrize(
    "changes",
    [
        {"record_bytes": 0},
        {"project_bytes": True},
        {"busy_timeout_ms": 60001},
        {"record_bytes": 10, "blob_bytes": 5},
    ],
)
def test_storage_policy_rejects_invalid_budgets(changes):
    with pytest.raises(InvalidRecord):
        StoragePolicy(**changes)


@pytest.mark.parametrize("revision", [-1, True, 2**63, 0.5])
def test_invalid_input_revision_never_saves(store, project, revision):
    with pytest.raises(InvalidRecord):
        _save(store, project.project_id, input_revision=revision)
    assert _counts(store)[2] == 0


@pytest.mark.parametrize(
    "title,mission",
    [
        ("", ""),
        ("x" * 241, ""),
        ("Valid", "x" * 8193),
        ("Invalid\x00", ""),
        ("Invalid\ud800", ""),
    ],
)
def test_project_metadata_rejects_invalid_values(store, title, mission):
    with pytest.raises(InvalidRecord):
        store.create_project(
            OWNER, title=title, mission=mission, operation_id="invalid-metadata"
        )
    assert _counts(store)[0] == 0


def test_mapping_cycle_string_budget_and_invalid_unicode_refused():
    cycle = {}
    cycle["self"] = cycle
    for value in (
        cycle,
        {"large": "x" * (16 * 1024 * 1024 + 1)},
        {"invalid": "\ud800"},
    ):
        with pytest.raises(InvalidRecord):
            RecordPayload.from_mapping(value, "test.record.v1")
    with pytest.raises(InvalidRecord):
        RecordPayload(b'{"invalid":"\\ud800"}', "test.record.v1").validate(
            StoragePolicy()
        )


def test_project_metadata_budget_failure_rolls_back_entire_creation(tmp_path):
    bounded = SQLiteProjectRepository(
        tmp_path / "tiny", policy=StoragePolicy(project_bytes=50)
    )
    with pytest.raises(QuotaExceeded):
        bounded.create_project(
            OWNER, title="Must not partially exist", operation_id="create"
        )
    assert _counts(bounded) == (0, 0, 0, 0, 0)


def test_event_metadata_budget_failure_keeps_prior_head_and_orphan(store, project):
    # Existing metadata is already larger than this new safety policy. Reading
    # remains possible, but adding any new metadata must reject without eviction.
    bounded = SQLiteProjectRepository(
        store.files.root, policy=StoragePolicy(project_bytes=100)
    )
    with pytest.raises(QuotaExceeded):
        _save(bounded, project.project_id)
    assert _counts(store)[2] == 0
    assert bounded.get_project(OWNER, project.project_id) == project
    assert (store.files.blobs / PAYLOAD.content_hash).exists()


def test_db_lock_contention_is_typed_and_replay_does_not_duplicate(store, project):
    short = SQLiteProjectRepository(
        store.files.root, policy=replace(store.policy, busy_timeout_ms=30)
    )
    with sqlite3.connect(store.path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        with pytest.raises(StoreUnavailable):
            _save(short, project.project_id)
        connection.rollback()
    assert _save(short, project.project_id).head.version == 1
    assert _save(short, project.project_id).head.version == 1


def test_disk_full_before_blob_sync_never_references_partial_bytes(
    store, project, monkeypatch
):
    def full(_fd):
        raise OSError(errno.ENOSPC, "injected disk full")

    with monkeypatch.context() as scoped:
        scoped.setattr(file_io.os, "fsync", full)
        with pytest.raises(QuotaExceeded):
            _save(store, project.project_id)
    assert _counts(store)[2] == 0
    assert list(store.files.staging.iterdir())
    assert not list(store.files.blobs.iterdir())
    assert _save(store, project.project_id).head.version == 1


def test_hostile_sqlite_sidecar_refused_before_recovery(store, project, tmp_path):
    target = tmp_path / "external-sidecar-target"
    target.write_bytes(b"not a journal; must not be touched")
    sidecar = store.path.with_name(store.path.name + "-journal")
    sidecar.symlink_to(target)
    with pytest.raises(IntegrityFailure):
        _save(store, project.project_id)
    assert target.read_bytes() == b"not a journal; must not be touched"


def test_live_blob_directory_alias_is_rejected_before_source_read(
    store, project, tmp_path
):
    _save(store, project.project_id)
    moved = tmp_path / "outside"
    store.files.blobs.rename(moved)
    store.files.blobs.symlink_to(moved, target_is_directory=True)
    with pytest.raises(IntegrityFailure):
        store.get_snapshot(
            OWNER, project.project_id, domain="propulsion", object_id="design-1"
        )


def test_revoked_member_cannot_replay_old_success(store, project):
    shared = store.set_member(
        OWNER,
        project.project_id,
        member=OTHER,
        capability=Membership.EDITOR,
        expected=project.head,
        operation_id="grant",
    )
    saved = store.save_snapshot(
        OTHER,
        project.project_id,
        domain="propulsion",
        object_id="design-1",
        input_revision=17,
        payload=PAYLOAD,
        expected=Head.absent(),
        operation_id="other-save",
    )
    store.set_member(
        OWNER,
        project.project_id,
        member=OTHER,
        capability=None,
        expected=shared.head,
        operation_id="revoke",
    )
    with pytest.raises(AccessDenied):
        store.save_snapshot(
            OTHER,
            project.project_id,
            domain="propulsion",
            object_id="design-1",
            input_revision=17,
            payload=PAYLOAD,
            expected=Head.absent(),
            operation_id="other-save",
        )
    assert (
        store.get_snapshot(
            OWNER, project.project_id, domain="propulsion", object_id="design-1"
        )
        == saved
    )


def test_project_version_conflicts_and_idempotent_metadata_receipts(store, project):
    renamed = store.change_project(
        OWNER,
        project.project_id,
        title="Renamed",
        expected=project.head,
        operation_id="rename",
    )
    assert (
        store.change_project(
            OWNER,
            project.project_id,
            title="Renamed",
            expected=project.head,
            operation_id="rename",
        )
        == renamed
    )
    with pytest.raises(HeadConflict):
        store.change_project(
            OWNER,
            project.project_id,
            title="Lost update",
            expected=project.head,
            operation_id="stale-rename",
        )
    assert store.get_project(OWNER, project.project_id) == renamed


def test_project_pages_are_authorized_and_bounded(store, project):
    another = store.create_project(OWNER, title="Second", operation_id="second")
    store.create_project(OTHER, title="Not mine", operation_id="other")
    first_page = store.list_projects(OWNER, limit=1)
    second_page = store.list_projects(OWNER, limit=1, after_id=first_page[0].project_id)
    assert {first_page[0].project_id, second_page[0].project_id} == {
        project.project_id,
        another.project_id,
    }
    for invalid in (0, 201, True):
        with pytest.raises(InvalidRecord):
            store.list_projects(OWNER, limit=invalid)
        with pytest.raises(InvalidRecord):
            store.list_commit_ids(
                OWNER,
                project.project_id,
                domain="propulsion",
                object_id="design-1",
                limit=invalid,
            )


def test_tombstoned_project_hidden_from_nonowner_and_recoverable_by_owner(
    store, project
):
    shared = store.set_member(
        OWNER,
        project.project_id,
        member=OTHER,
        capability=Membership.EDITOR,
        expected=project.head,
        operation_id="grant",
    )
    deleted = store.change_project(
        OWNER,
        project.project_id,
        lifecycle=Lifecycle.DELETED,
        expected=shared.head,
        confirmation_project_id=project.project_id,
        operation_id="delete",
    )
    assert store.list_projects(OTHER) == ()
    assert store.get_project(OWNER, project.project_id) == deleted
    with pytest.raises(AccessDenied):
        store.get_project(OTHER, project.project_id)


def test_database_pragmas_and_schema_guard_are_checked_on_every_connection(store):
    with store._transaction() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        assert connection.execute("PRAGMA synchronous").fetchone()[0] == 2
    with sqlite3.connect(store.path) as connection:
        connection.execute("DROP TRIGGER immutable_operations_delete")
    with pytest.raises(SchemaMismatch):
        store.list_projects(OWNER)


def test_private_blob_primitive_rejects_path_digest_before_install(store):
    with pytest.raises(IntegrityFailure):
        store.files.install_blob(PAYLOAD.data, "../outside")
    with pytest.raises(InvalidRecord):
        RecordPayload(PAYLOAD.data, "test.record.v1", source_namespace=0).validate(
            StoragePolicy()
        )


def test_second_process_coordinator_is_excluded(store):
    code = """
import sys
from pathlib import Path
from infrastructure.persistence.files import CoordinatorLease
from systems.projects.authority import StoreUnavailable
try:
    lease=CoordinatorLease(Path(sys.argv[1]))
except StoreUnavailable:
    print('excluded')
else:
    lease.close()
    raise SystemExit(1)
"""
    with CoordinatorLease(store.files.root):
        result = subprocess.run(
            [sys.executable, "-c", code, str(store.files.root)],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "excluded"


def test_inactive_member_can_be_revoked_but_cannot_be_granted_access(store, project):
    shared = store.set_member(
        OWNER,
        project.project_id,
        member=OTHER,
        capability=Membership.EDITOR,
        expected=project.head,
        operation_id="grant",
    )
    inactive = replace(OTHER, active=False)
    with pytest.raises(AccessDenied):
        store.set_member(
            OWNER,
            project.project_id,
            member=inactive,
            capability=Membership.VIEWER,
            expected=shared.head,
            operation_id="grant-inactive",
        )
    revoked = store.set_member(
        OWNER,
        project.project_id,
        member=inactive,
        capability=None,
        expected=shared.head,
        operation_id="revoke-inactive",
    )
    assert revoked.head.version == shared.head.version + 1
    with pytest.raises(AccessDenied):
        store.get_project(OTHER, project.project_id)
