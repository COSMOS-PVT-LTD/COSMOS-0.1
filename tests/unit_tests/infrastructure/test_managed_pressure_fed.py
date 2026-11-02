"""Isolated pressure-fed authority/recovery; synthetic software inputs only."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from threading import Barrier

import pytest

from api.pressure_fed import assess_pressure_fed
from api.pressure_fed_projects import methods
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import (
    AccessDenied,
    HeadConflict,
    OperationConflict,
    Principal,
    StoreUnavailable,
)
from systems.projects.pressure_fed import DOMAIN, INPUTS, ManagedPressureFed
from systems.projects.propulsion_authority import (
    PropulsionProjectService,
    decode_design,
)
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (  # noqa: F401
    baseline,
    isolated_catalog,
    specification,
)

OWNER = Principal("USR-pressure-fed-owner", "ENGINEER")


@pytest.fixture
def setup(tmp_path, request):
    design = request.getfixturevalue("baseline")
    repo = SQLiteProjectRepository(tmp_path)
    project = repo.create_project(
        OWNER, title="Synthetic pressure-fed software QA", operation_id="project"
    )
    source = PropulsionProjectService(repo).create(
        OWNER,
        project.project_id,
        design=design,
        operation_id="source",
        command_hash="1" * 64,
    )
    return repo, project.project_id, source, specification(decode_design(source))


def create(service, project, source, spec, **edits):
    return service.create(
        OWNER,
        project,
        source.commit_id,
        source.head,
        spec,
        edits.get("operation", "assessment"),
        edits.get("hashed", "2" * 64),
    )


def test_exact_bytes_replay_restart_and_independent_source_unchanged(setup):
    repo, project, source, spec = setup
    spec["streams"]["fuel"]["density"]["value"] = 999.1234567890123
    service = ManagedPressureFed(repo, assess_pressure_fed, methods)
    result = create(service, project, source, spec)
    record = service.read(OWNER, result)
    assert record["record"]["status"] == "COMPLETED" and record["upstream_current"]
    assert record["record"]["command"]["specification"] == spec
    assert record["record"]["baseline_canonical_json"].encode() == source.payload
    inputs = repo.resolve_snapshot(OWNER, project, result.input_commit_id)
    assert inputs.domain == INPUTS
    assert json.loads(inputs.payload)["command"]["specification"] == spec
    assert create(service, project, source, spec).payload == result.payload
    with pytest.raises(OperationConflict):
        create(service, project, source, spec, hashed="3" * 64)
    reopened = SQLiteProjectRepository(repo.files.root)
    after = ManagedPressureFed(reopened, assess_pressure_fed, methods)
    assert (
        after.read(
            OWNER,
            reopened.get_snapshot(
                OWNER, project, domain=DOMAIN, object_id=result.object_id
            ),
        )
        == record
    )
    assert (
        reopened.get_snapshot(
            OWNER, project, domain="propulsion", object_id=source.object_id
        ).payload
        == source.payload
    )


def test_terminal_failure_has_inputs_but_no_calculated_answer_and_replay_does_not_rerun(
    setup,
):
    repo, project, source, spec = setup
    calls = []

    def broken(*_):
        calls.append(1)
        raise RuntimeError("synthetic evaluator failure")

    service = ManagedPressureFed(repo, broken, methods)
    saved = create(service, project, source, spec)
    value = service.read(OWNER, saved)
    assert (
        value["record"]["status"] == "FAILED" and value["record"]["evaluation"] is None
    )
    assert value["record"]["failure"]["code"] == "RuntimeError"
    assert not value["usable_current_assessment"]
    assert create(service, project, source, spec) == saved and len(calls) == 1
    assert (
        service.read_input(
            OWNER, repo.resolve_snapshot(OWNER, project, saved.input_commit_id)
        )["terminal_commit_id"]
        == saved.commit_id
    )


def test_input_first_interruption_resume_consumes_original_even_after_baseline_edit(
    setup,
):
    repo, project, source, spec = setup

    class Interrupted(BaseException):
        pass

    def interrupted(*_):
        raise Interrupted()

    service = ManagedPressureFed(repo, interrupted, methods)
    with pytest.raises(Interrupted):
        create(service, project, source, spec)
    items = repo.list_objects(OWNER, project, domain=INPUTS)
    assert len(items) == 1 and not repo.list_objects(OWNER, project, domain=DOMAIN)
    capture = repo.get_snapshot(
        OWNER, project, domain=INPUTS, object_id=items[0].object_id
    )
    assert service.read_input(OWNER, capture)["terminal_commit_id"] is None
    changed = PropulsionProjectService(repo).edit(
        OWNER,
        project,
        source.object_id,
        expected=source.head,
        operation_id="newer",
        command_hash="3" * 64,
        mutate=lambda d: setattr(d, "name", "Later unrelated selected input"),
    )
    after = ManagedPressureFed(
        SQLiteProjectRepository(repo.files.root), assess_pressure_fed, methods
    )
    saved = create(after, project, source, spec)
    record = after.read(OWNER, saved)
    assert record["record"]["baseline_canonical_json"].encode() == source.payload
    assert not record["upstream_current"] and record["record"]["status"] == "COMPLETED"
    assert (
        repo.get_snapshot(
            OWNER, project, domain="propulsion", object_id=source.object_id
        )
        == changed
    )
    with pytest.raises(HeadConflict):
        create(after, project, source, spec, operation="new-operation", hashed="4" * 64)


def test_late_baseline_edit_is_retained_as_historical_not_promoted(setup):
    repo, project, source, spec = setup

    def evaluate(design, config):
        PropulsionProjectService(repo).edit(
            OWNER,
            project,
            source.object_id,
            expected=source.head,
            operation_id="edit-during",
            command_hash="3" * 64,
            mutate=lambda d: setattr(d, "name", "Late edit"),
        )
        return assess_pressure_fed(design, config)

    service = ManagedPressureFed(repo, evaluate, methods)
    value = service.read(OWNER, create(service, project, source, spec))
    assert value["record"]["status"] == "COMPLETED" and not value["upstream_current"]


@pytest.mark.parametrize("moment", ["before", "during", "resume"])
def test_method_drift_is_not_published_as_a_calculated_answer(setup, moment):
    repo, project, source, spec = setup
    current = {"scientific-source": "a" * 64}

    class Interrupted(BaseException):
        pass

    def evaluate(design, config):
        if moment == "resume":
            raise Interrupted()
        answer = assess_pressure_fed(design, config)
        current["scientific-source"] = "b" * 64
        return answer

    service = ManagedPressureFed(repo, evaluate, lambda: dict(current))
    if moment == "before":
        current["scientific-source"] = "b" * 64
        with pytest.raises(StoreUnavailable):
            create(service, project, source, spec)
        assert not repo.list_objects(OWNER, project, domain=INPUTS)
    elif moment == "resume":
        with pytest.raises(Interrupted):
            create(service, project, source, spec)
        current["scientific-source"] = "b" * 64
        restarted = ManagedPressureFed(repo, assess_pressure_fed, lambda: dict(current))
        with pytest.raises(StoreUnavailable):
            create(restarted, project, source, spec)
    else:
        value = service.read(OWNER, create(service, project, source, spec))
        assert (
            value["record"]["evaluation"] is None
            and value["record"]["status"] == "FAILED"
        )
        assert not value["upstream_current"]


@pytest.mark.parametrize(
    "actor",
    [
        Principal("other", "ENGINEER"),
        Principal(OWNER.user_id, "VIEWER"),
        Principal(OWNER.user_id, "ENGINEER", False),
    ],
)
def test_unauthorized_write_cannot_capture_or_evaluate(setup, actor):
    repo, project, source, spec = setup
    calls = []
    service = ManagedPressureFed(repo, lambda *_: calls.append(1), methods)
    with pytest.raises(AccessDenied):
        service.create(
            actor, project, source.commit_id, source.head, spec, "denied", "4" * 64
        )
    assert not calls and not repo.list_objects(OWNER, project, domain=INPUTS)


def test_invalid_spec_does_not_leave_accepted_inputs_or_outputs(setup):
    repo, project, source, spec = setup
    original = deepcopy(spec)
    spec["streams"]["fuel"]["density"]["unit"] = "bar"
    from systems.projects.authority import InvalidRecord

    with pytest.raises(InvalidRecord):
        create(
            ManagedPressureFed(repo, assess_pressure_fed, methods),
            project,
            source,
            spec,
        )
    assert not repo.list_objects(OWNER, project, domain=INPUTS)
    assert original["streams"]["fuel"]["density"]["unit"] == "kg/m3"


def test_forged_or_changed_evaluation_context_is_failed_not_published(setup):
    repo, project, source, spec = setup

    def wrong(design, config):
        value = assess_pressure_fed(design, config)
        value["result"]["outputs"]["workflow_cycle_complete"] = True
        return value

    service = ManagedPressureFed(repo, wrong, methods)
    value = service.read(OWNER, create(service, project, source, spec))
    assert (
        value["record"]["evaluation"] is None
        and value["record"]["failure"]["code"] == "IntegrityFailure"
    )


@pytest.mark.parametrize("which", ["design", "specification"])
def test_evaluator_cannot_relabel_mutated_sources_as_original_capture(setup, which):
    repo, project, source, spec = setup
    original = deepcopy(spec)

    def mutate(design, config):
        if which == "design":
            design.name = "Evaluator attempted to change original"
        else:
            config["streams"]["fuel"]["density"]["value"] = 900
        return assess_pressure_fed(design, config)

    service = ManagedPressureFed(repo, mutate, methods)
    value = service.read(OWNER, create(service, project, source, spec))
    assert value["record"]["evaluation"] is None
    assert value["record"]["command"]["specification"] == original == spec
    assert value["record"]["baseline_canonical_json"].encode() == source.payload


def test_concurrent_same_command_has_one_terminal_receipt(setup):
    repo, project, source, spec = setup
    barrier = Barrier(2)

    def evaluate(design, config):
        barrier.wait(timeout=10)
        return assess_pressure_fed(design, config)

    service = ManagedPressureFed(repo, evaluate, methods)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(lambda _: create(service, project, source, spec), range(2))
        )
    assert results[0] == results[1]
    assert len(repo.list_objects(OWNER, project, domain=DOMAIN)) == 1
    assert len(repo.list_objects(OWNER, project, domain=INPUTS)) == 1


def test_actual_process_kill_after_input_capture_recovers_exact_command(
    setup, tmp_path
):
    repo, project, source, spec = setup
    marker = tmp_path / "child-captured.marker"
    arguments = json.dumps(
        {
            "root": str(repo.files.root),
            "project": project,
            "commit": source.commit_id,
            "head": {
                "version": source.head.version,
                "content_hash": source.head.content_hash,
            },
            "spec": spec,
            "marker": str(marker),
        }
    )
    code = """
import json,sys,time
from pathlib import Path
from api.pressure_fed_projects import methods
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import Head,Principal
from systems.projects.pressure_fed import ManagedPressureFed
data=json.loads(sys.argv[1])
def pause(design,specification):
    Path(data["marker"]).write_text("inputs durably captured")
    time.sleep(30)
service=ManagedPressureFed(SQLiteProjectRepository(Path(data["root"])),pause,methods)
service.create(Principal("USR-pressure-fed-owner","ENGINEER"),data["project"],data["commit"],Head(**data["head"]),data["spec"],"assessment","2"*64)
"""
    process = subprocess.Popen(
        [sys.executable, "-c", code, arguments],
        cwd=Path(__file__).resolve().parents[3],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 12
        while (
            not marker.exists()
            and process.poll() is None
            and time.monotonic() < deadline
        ):
            time.sleep(0.02)
        assert marker.exists(), process.communicate(timeout=2)
        process.kill()
        process.communicate(timeout=5)
        assert process.returncode != 0
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
    assert not repo.list_objects(OWNER, project, domain=DOMAIN)
    before = repo.get_snapshot(
        OWNER,
        project,
        domain=INPUTS,
        object_id=repo.list_objects(OWNER, project, domain=INPUTS)[0].object_id,
    )
    after = ManagedPressureFed(
        SQLiteProjectRepository(repo.files.root), assess_pressure_fed, methods
    )
    saved = create(after, project, source, spec)
    assert saved.input_commit_id == before.commit_id
    assert after.read(OWNER, saved)["record"]["status"] == "COMPLETED"
