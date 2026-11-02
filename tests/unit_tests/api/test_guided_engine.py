"""Real supervised worker and isolated durable authority. No live roots."""

import time
from copy import deepcopy

import pytest

from api.project_authority import principal
from core.exceptions import InvalidInputError
from gui.server import CosmosApplication
from systems.persistence.job_repository import TERMINAL
from systems.projects.authority import InvalidRecord, RecordNotFound, StoreUnavailable
from tests.unit_tests.systems_layer.test_guided_engine import engine_brief


@pytest.fixture
def setup(tmp_path):
    app = CosmosApplication(tmp_path, new_shell=True, durable_projects=True)
    user = next(u for u in app.auth.list_users() if u.login_id == "cosmos-admin")
    api = app.project_api
    project = api.handle(
        user,
        "POST",
        [],
        {},
        {
            "title": "Guided software QA",
            "mission": "NOT hardware evidence",
            "operation_id": "project",
        },
    )["project"]["project_id"]
    yield app, api, user, project
    app.close()


def command(setup, path, body=None, query=None):
    _, api, user, project = setup
    return api.handle(
        user,
        "GET" if body is None else "POST",
        [project, "guided-engine", *path],
        query or {},
        body or {},
    )


def accept(setup):
    request = {
        "brief": engine_brief(),
        "overrides": {"mixture_ratio": {"value": 2.63, "unit": "1"}},
        "profile_id": "methalox-pf-preliminary-v1",
    }
    preview = command(setup, ["preview"], request)
    return command(
        setup,
        [],
        {
            **request,
            "review_hash": preview["resolution"]["review_hash"],
            "operation_id": "accept",
        },
    )


def wait_for(setup, path):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        r = command(setup, path)
        if r["state"] in {s.value for s in TERMINAL}:
            return r
        time.sleep(0.05)
    pytest.fail("Bounded isolated guided run did not finish")


def test_acceptance_run_exact_replay_and_expert_handoff(setup):
    _app, api, user, project = setup
    a = accept(setup)
    assert accept(setup) == a
    path = [a["authority"]["object_id"], "jobs"]
    body = {"expected": a["authority"]["head"], "operation_id": "calculate"}
    job = command(setup, path, body)
    r = wait_for(setup, [*path, job["job_id"]])
    assert r["state"] == "COMPLETED", r
    assert r["result_current"]
    assert r["result"]["report"]["calculated_thrust_n"] == pytest.approx(1500, rel=2e-4)
    assert command(setup, path, body)["job_id"] == job["job_id"]
    d = api.handle(
        user, "GET", [project, "designs", r["result"]["design_object_id"]], {}, {}
    )
    assert d["authority"]["commit_id"] == r["result"]["design_commit_id"]
    assert d["design"]["requirements"]["target_thrust"]["magnitude"] == 1500
    assert d["design"]["thermochemistry_configuration"]["mode"] == "nasa_cea"
    assert (
        a["authority"]["commit_id"]
        == command(setup, [a["authority"]["object_id"]])["authority"]["commit_id"]
    )
    assert (
        len(api.repository.list_objects(principal(user), project, domain="propulsion"))
        == 1
    )
    exported = api.handle(
        user, "GET", [project, "designs", d["design"]["design_id"], "export"], {}, {}
    )
    assert exported["ok"]


def test_changed_review_rejected_before_any_saved_acceptance(setup):
    request = {
        "brief": engine_brief(),
        "overrides": {},
        "profile_id": "methalox-pf-preliminary-v1",
    }
    p = command(setup, ["preview"], request)
    request["brief"]["thrust"]["value"] = 2000
    with pytest.raises(InvalidRecord, match="changed"):
        command(
            setup,
            [],
            {
                **request,
                "review_hash": p["resolution"]["review_hash"],
                "operation_id": "tamper",
            },
        )
    assert command(setup, [])["inputs"] == []


def test_cancelled_attempt_keeps_inputs_and_never_publishes_design(setup, monkeypatch):
    a = accept(setup)
    service = setup[1].guided.service
    # Hold the actual supervised subprocess until the cancellation arrives.
    from infrastructure.geometry import WorkerCommand

    runner = service.runner
    runner.command = WorkerCommand(("/bin/sleep", "4"))
    path = [a["authority"]["object_id"], "jobs"]
    job = command(
        setup, path, {"expected": a["authority"]["head"], "operation_id": "run-cancel"}
    )
    deadline = time.monotonic() + 2
    exact = command(setup, [*path, job["job_id"]])
    while exact["state"] == "QUEUED" and time.monotonic() < deadline:
        time.sleep(0.01)
        exact = command(setup, [*path, job["job_id"]])
    assert exact["state"] == "RUNNING"
    command(
        setup,
        [*path, job["job_id"], "cancel"],
        {"expected": exact["head"], "operation_id": "cancel"},
    )
    r = wait_for(setup, [*path, job["job_id"]])
    assert r["state"] == "CANCELLED"
    assert not setup[1].repository.list_objects(
        principal(setup[2]), setup[3], domain="propulsion"
    )


def test_source_drift_or_worker_failure_cannot_publish_a_success(setup):
    a = accept(setup)
    service = setup[1].guided.service
    service.runner.command = __import__(
        "infrastructure.geometry", fromlist=["WorkerCommand"]
    ).WorkerCommand(("/usr/bin/false",))
    path = [a["authority"]["object_id"], "jobs"]
    job = command(
        setup, path, {"expected": a["authority"]["head"], "operation_id": "fails"}
    )
    r = wait_for(setup, [*path, job["job_id"]])
    assert r["state"] == "FAILED" and "report" not in r["result"]
    service.methods = lambda: {"changed-source": "a" * 64}
    with pytest.raises(StoreUnavailable, match="changed"):
        command(
            setup, path, {"expected": a["authority"]["head"], "operation_id": "drift"}
        )


def test_query_injection_cross_project_and_wrong_job_scope_refused(setup):
    a = accept(setup)
    with pytest.raises(InvalidRecord):
        command(setup, ["capabilities"], query={"runtime": ["/tmp/evil"]})
    _, api, user, _ = setup
    other = api.handle(
        user,
        "POST",
        [],
        {},
        {"title": "Other project", "mission": "", "operation_id": "other"},
    )["project"]["project_id"]
    with pytest.raises(RecordNotFound):
        api.handle(
            user, "GET", [other, "guided-engine", a["authority"]["object_id"]], {}, {}
        )
    b = deepcopy(engine_brief())
    b["worker"] = "untrusted"
    with pytest.raises(InvalidInputError):
        command(
            setup,
            ["preview"],
            {"brief": b, "overrides": {}, "profile_id": "methalox-pf-preliminary-v1"},
        )
