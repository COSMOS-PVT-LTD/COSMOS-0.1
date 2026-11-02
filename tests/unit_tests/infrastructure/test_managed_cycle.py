"""Selected-cycle authority reuse, original captures, restart and currentness."""

import json

import pytest

from api.cycle_assessment import evaluate, methods
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import AccessDenied, Principal
from systems.projects.cycle_assessment import ManagedCycleAssessment
from systems.projects.propulsion_authority import (
    PropulsionProjectService,
    decode_design,
)
from tests.fixtures.coupled_cycle import design, specification
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)

OWNER = Principal("cycle-owner", "ENGINEER")


def prepared(tmp_path):
    repo = SQLiteProjectRepository(tmp_path)
    project = repo.create_project(
        OWNER, title="Synthetic coupled cycle QA", operation_id="p"
    )
    source = PropulsionProjectService(repo).create(
        OWNER,
        project.project_id,
        design=design(cooling=True, film=True),
        operation_id="b",
        command_hash="1" * 64,
    )
    spec = specification(decode_design(source), cooling=True, film=True)
    return repo, project.project_id, source, spec


def create(service, project, source, spec):
    return service.create(
        OWNER, project, source.commit_id, source.head, spec, "calculation", "2" * 64
    )


def test_exact_capture_restart_replay_and_unbalanced_not_qualified(tmp_path):
    repo, project, source, spec = prepared(tmp_path)
    service = ManagedCycleAssessment(repo, evaluate, methods)
    saved = create(service, project, source, spec)
    value = service.read(OWNER, saved)
    assert value["record"]["status"] == "COMPLETED", value["record"]["failure"]
    assert value["usable_current_balanced_assessment"]
    assert value["record"]["baseline_canonical_json"].encode() == source.payload
    assert (
        json.loads(
            repo.resolve_snapshot(OWNER, project, saved.input_commit_id).payload
        )["command"]["specification"]
        == spec
    )
    assert create(service, project, source, spec).payload == saved.payload
    reopened = SQLiteProjectRepository(repo.files.root)
    assert (
        ManagedCycleAssessment(reopened, evaluate, methods).read(OWNER, saved) == value
    )
    spec["gas_generator"]["net_released_energy"]["value"] += 100
    unbalanced = service.create(
        OWNER, project, source.commit_id, source.head, spec, "different", "3" * 64
    )
    assert not service.read(OWNER, unbalanced)["usable_current_balanced_assessment"]


def test_interrupted_capture_recovers_original_and_failure_has_no_answer(tmp_path):
    repo, project, source, spec = prepared(tmp_path)

    class Interrupted(BaseException):
        pass

    def interrupted(*_):
        raise Interrupted()

    with pytest.raises(Interrupted):
        create(
            ManagedCycleAssessment(repo, interrupted, methods), project, source, spec
        )
    captures = repo.list_objects(OWNER, project, domain="coupled-cycle-inputs")
    assert len(captures) == 1 and not repo.list_objects(
        OWNER, project, domain="coupled-cycle-assessment"
    )
    recovered = create(
        ManagedCycleAssessment(repo, evaluate, methods), project, source, spec
    )
    assert json.loads(recovered.payload)["status"] == "COMPLETED"
    spec["gas_generator"]["maximum_flow"]["value"] = 1e-12
    failed = ManagedCycleAssessment(repo, evaluate, methods).create(
        OWNER, project, source.commit_id, source.head, spec, "infeasible", "4" * 64
    )
    assert json.loads(failed.payload)["status"] == "FAILED"
    assert json.loads(failed.payload)["evaluation"] is None


def test_method_drift_demotes_original_and_foreign_actor_cannot_read(tmp_path):
    repo, project, source, spec = prepared(tmp_path)
    identity = {"synthetic-test-method": "a" * 64}
    service = ManagedCycleAssessment(repo, evaluate, lambda: dict(identity))
    saved = create(service, project, source, spec)
    original = saved.payload
    identity["synthetic-test-method"] = "b" * 64
    assert not service.read(OWNER, saved)["upstream_current"]
    assert saved.payload == original
    with pytest.raises(AccessDenied):
        service.read(Principal("foreign", "ENGINEER"), saved)
