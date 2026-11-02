"""Exact managed plans/data/comparison and fail-closed physical evidence gates."""

import base64
import json

import pytest

from api.propulsion_validation import methods
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import (
    AccessDenied,
    HeadConflict,
    InvalidRecord,
    Principal,
    StoreUnavailable,
)
from systems.projects.propulsion_authority import PropulsionProjectService
from systems.projects.propulsion_validation import PropulsionValidation, candidate
from tests.fixtures.coupled_cycle import design
from tests.fixtures.propulsion_validation import csv_data, metadata, specification
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)

ACTOR = Principal("propulsion-vv-owner", "ENGINEER")


def setup(tmp_path):
    repo = SQLiteProjectRepository(tmp_path)
    project = repo.create_project(
        ACTOR, title="Synthetic validation workflow only", operation_id="p"
    )
    source = PropulsionProjectService(repo).create(
        ACTOR,
        project.project_id,
        design=design(cooling=True),
        operation_id="b",
        command_hash="1" * 64,
    )
    service = PropulsionValidation(repo, methods)
    basis = candidate(source, ["thrust", "coolant_outlet_temperature"])
    body = {
        "baseline_commit_id": source.commit_id,
        "expected_baseline": {
            "version": source.head.version,
            "content_hash": source.head.content_hash,
        },
        "specification": specification(basis),
        "operation_id": "plan",
    }
    return repo, project.project_id, source, service, body


def test_plan_before_data_exact_replay_comparison_and_restart(tmp_path):
    repo, project, source, service, body = setup(tmp_path)
    plan = service.create(ACTOR, project, "plans", body, "2" * 64)
    value = service.read(ACTOR, plan)
    assert value["record"]["readiness"] == "AWAITING_MEASUREMENTS"
    assert (
        value["record"]["candidate"]["baseline_canonical_json"].encode()
        == source.payload
    )
    assert (
        service.create(ACTOR, project, "plans", body, "2" * 64).payload == plan.payload
    )
    raw = csv_data(value["record"])
    data_body = {
        "plan_commit_id": plan.commit_id,
        "csv_base64": base64.b64encode(raw).decode(),
        "provenance": metadata(),
        "operation_id": "data",
    }
    data = service.create(ACTOR, project, "measurements", data_body, "3" * 64)
    assert base64.b64decode(json.loads(data.payload)["csv_base64"]) == raw
    assessment = service.create(
        ACTOR,
        project,
        "assessments",
        {
            "plan_commit_id": plan.commit_id,
            "measurement_commit_id": data.commit_id,
            "operation_id": "assessment",
        },
        "4" * 64,
    )
    result = service.read(ACTOR, assessment)
    assert result["record"]["software_comparison_passed"] and result["upstream_current"]
    assert (
        result["physical_validation"] == "NOT_PERFORMED"
        and not result["independent_acceptance"]
    )
    reopened = SQLiteProjectRepository(repo.files.root)
    assert PropulsionValidation(reopened, methods).read(ACTOR, assessment) == result
    assert (
        repo.resolve_snapshot(ACTOR, project, source.commit_id).payload
        == source.payload
    )


def test_wrong_head_posted_authority_foreign_actor_and_method_drift(tmp_path):
    repo, project, _source, service, body = setup(tmp_path)
    original_head = body["expected_baseline"]
    body["expected_baseline"] = {"version": 0, "content_hash": "0" * 64}
    with pytest.raises(HeadConflict):
        service.create(ACTOR, project, "plans", body, "2" * 64)
    body["expected_baseline"] = original_head
    with pytest.raises(InvalidRecord):
        service.create(
            ACTOR, project, "plans", {**body, "independent_acceptance": True}, "3" * 64
        )
    plan = service.create(ACTOR, project, "plans", body, "4" * 64)
    with pytest.raises(AccessDenied):
        service.read(Principal("foreign", "ENGINEER"), plan)
    with pytest.raises(AccessDenied):
        service.create(
            Principal(ACTOR.user_id, "VIEWER"), project, "plans", body, "5" * 64
        )
    different = PropulsionValidation(repo, lambda: {"changed": "a" * 64})
    assert not different.read(ACTOR, plan)["upstream_current"]
    identity = {"test": "1" * 64}
    changed = PropulsionValidation(repo, lambda: dict(identity))
    identity["test"] = "2" * 64
    with pytest.raises(StoreUnavailable):
        changed.create(
            ACTOR, project, "plans", {**body, "operation_id": "new"}, "6" * 64
        )
