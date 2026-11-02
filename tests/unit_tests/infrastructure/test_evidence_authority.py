"""Isolated ledger contracts; synthetic fixtures are not native/physical proof."""
from __future__ import annotations

from contextlib import nullcontext
from dataclasses import asdict
from uuid import uuid4

import pytest

from infrastructure.persistence.durable_jobs import SQLiteJobRepository
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.contracts.geometry._wire import GeometryContractError
from systems.projects.authority import (
    AccessDenied,
    Head,
    HeadConflict,
    OperationConflict,
    Principal,
)
from systems.projects.evidence_authority import (
    LEDGER,
    LEDGER_ID,
    ManagedEvidence,
    decode,
    unpack_session,
)
from tests.fixtures.vv_cases import criteria, dataset
from validation.workbench import ComparisonWorkbench

OWNER = Principal("USR-evidence-test", "ENGINEER")


def setup(root):
    repo = SQLiteProjectRepository(root)
    project = repo.create_project(OWNER, title="Synthetic ledger — not hardware", operation_id="create")
    return repo, project, ManagedEvidence(repo, SQLiteJobRepository(repo), lambda _: nullcontext())


def command(service, project, action, value, head=None, nonce=None, hashed="a"*64):
    return service.command(OWNER, project.project_id, action, value, expected=head or Head.absent(), operation_id=nonce or str(uuid4()), command_hash=hashed)


def test_exact_ordering_survives_repository_and_service_restart(tmp_path):
    repo, project, service = setup(tmp_path)
    first = command(service, project, "declare", {"criteria": criteria()})
    second = command(service, project, "import", {"dataset": dataset("analytic-reference", "2")}, first.head, hashed="b"*64)
    reopened = SQLiteProjectRepository(tmp_path)
    retained = reopened.get_snapshot(OWNER, project.project_id, domain=LEDGER, object_id=LEDGER_ID)
    assert retained.payload == second.payload
    s = unpack_session(decode(retained, LEDGER))
    assert s.policies[next(iter(s.policies))][1] < s.first_seen["2"*64]
    assert len(reopened.list_commit_ids(OWNER, project.project_id, domain=LEDGER, object_id=LEDGER_ID)) == 2
    assert repo.get_snapshot(OWNER, project.project_id, domain=LEDGER, object_id=LEDGER_ID, commit_id=first.commit_id).payload == first.payload


def test_reimport_does_not_reset_exposure_or_make_late_policy_predeclared(tmp_path):
    _, project, service = setup(tmp_path)
    first = command(service, project, "import", {"dataset": dataset("analytic-reference", "2")})
    second = command(service, project, "declare", {"criteria": criteria()}, first.head, hashed="b"*64)
    third = command(service, project, "import", {"dataset": dataset("analytic-reference", "2")}, second.head, hashed="c"*64)
    s = unpack_session(decode(third, LEDGER))
    assert s.first_seen["2"*64] == 1 and next(iter(s.policies.values()))[1] == 2
    worker = ComparisonWorkbench(tmp_path)
    try:
        worker.sessions[OWNER.user_id] = s
        candidate = worker.imported(OWNER.user_id, dataset())
        with pytest.raises(GeometryContractError, match="precede"):
            worker.assess(OWNER.user_id, candidate["dataset_id"], next(iter(s.datasets)), next(iter(s.policies)))
    finally:
        worker.close()


def test_ledger_cas_retries_and_collision_are_not_silently_rebased(tmp_path):
    _, project, service = setup(tmp_path)
    first = command(service, project, "declare", {"criteria": criteria()}, nonce="exact")
    assert command(service, project, "declare", {"criteria": criteria()}, nonce="exact") == first
    with pytest.raises(OperationConflict):
        command(service, project, "declare", {"criteria": criteria()}, nonce="exact", hashed="b"*64)
    with pytest.raises(HeadConflict):
        command(service, project, "import", {"dataset": dataset("analytic-reference", "2")}, Head.absent(), hashed="c"*64)


def test_ledger_ownership_and_scope_are_checked_before_returning_bytes(tmp_path):
    repo, project, service = setup(tmp_path)
    command(service, project, "declare", {"criteria": criteria()})
    with pytest.raises(AccessDenied):
        repo.get_snapshot(Principal("USR-unrelated", "ENGINEER"), project.project_id, domain=LEDGER, object_id=LEDGER_ID)


@pytest.mark.parametrize("value", [True, {}, {"dataset": dataset("simulation")}, {"dataset": {**dataset(), "production_handoff": True}}])
def test_import_never_accepts_posted_simulation_or_approval(value, tmp_path):
    _, project, service = setup(tmp_path)
    with pytest.raises((GeometryContractError, TypeError, KeyError)):
        command(service, project, "import", value)


def test_body_expected_head_is_a_storage_identity_not_domain_revision(tmp_path):
    _, project, service = setup(tmp_path)
    result = command(service, project, "declare", {"criteria": criteria()})
    assert asdict(result.head)["version"] == 1 and result.input_revision == 0
