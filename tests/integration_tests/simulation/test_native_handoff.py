"""Actual OCCT/independent STEP QA; optional pinned runtime, never fake success."""
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from api.ngg_workbench import runtime_config
from simulation.workbench import SimulationWorkbench
from systems.contracts.geometry._wire import GeometryContractError
from systems.geometry.workbench import GeometryWorkbench


@pytest.fixture
def native(tmp_path):
    path = os.environ.get("COSMOS_P09_NATIVE_CONFIG")
    if not path:
        pytest.skip("Explicit pinned local OCCT runtime required; normal CI must not invent native evidence")
    geometry = GeometryWorkbench(tmp_path.resolve(), runtime_config(Path(path)))
    solver = SimulationWorkbench()
    actor = "p09-native-test"
    context = geometry.context(actor)
    snapshot = context["snapshot"]["content_sha256"]
    job = geometry.build(actor, snapshot)["job_id"]
    _, future = geometry.owned(actor, job)
    future.result(timeout=60)
    assert geometry.status(actor, job)["fixture_exchange_eligible"] is True
    study = solver.attach(actor, geometry, job, snapshot)
    yield actor, geometry, solver, study, job, snapshot
    solver.close(); geometry.close()


def run(native):
    actor, geometry, solver, context, _, _ = native
    job = solver.submit(actor, geometry, context["study_id"])["run_id"]
    solver.owned(actor, job).future.result(timeout=10)
    return job, solver.status(actor, geometry, job)


def test_actual_geometry_handoff_and_repeated_study(native):
    job, status = run(native)
    result = status["result"]
    assert status["state"] == "completed" and status["freshness"] == "current"
    assert result["numerical_convergence"] == "converged" and result["conservation_checks"]["passed"] is True
    assert result["solution_verification"] == "analytic-benchmark-passed"
    assert result["experimental_validation"] == "not-performed" and result["production_handoff"] is False
    assert result["mesh"]["named_selection"]["mapping_status"] == "exact"
    assert len(status["events"]) >= 2
    _, repeated = run(native)
    assert repeated["result"]["temperature_k"] == result["temperature_k"]
    assert repeated["result"]["mesh"] == result["mesh"]
    assert job != repeated["run_id"]


def test_actual_nonconvergence_is_not_verification(native):
    actor, geometry, solver, context, _, _ = native
    settings = context["study"]["settings"]
    settings = {key: value for key, value in settings.items() if key not in {"schema_version", "content_sha256", "contract_type"}}
    settings["max_iterations"] = 1
    changed = solver.change(actor, context["study_id"], settings)
    job = solver.submit(actor, geometry, changed["study_id"])["run_id"]
    solver.owned(actor, job).future.result(timeout=10)
    result = solver.dataset(actor, job)
    assert result["execution_status"] == "completed" and result["termination_reason"] == "iteration_limit"
    assert result["numerical_convergence"] == "nonconverged" and result["solution_verification"] == "not-accepted"
    assert result["conservation_checks"]["passed"] is False and result["diagnostics"][0]["action"]


def test_actual_geometry_change_stales_old_result_and_blocks_new_run(native):
    actor, geometry, solver, context, _, snapshot = native
    job, _ = run(native)
    geometry.change(actor, snapshot, {"operation": "union", "backend": "occt", "voxel_m": .0005})
    assert solver.status(actor, geometry, job)["freshness"] == "stale"
    with pytest.raises(GeometryContractError, match="snapshot"):
        solver.submit(actor, geometry, context["study_id"])
    assert solver.dataset(actor, job)["study_id"] == context["study_id"]


def test_result_corruption_and_cross_actor_are_refused(native):
    actor, _, solver, _, _, _ = native
    job, _ = run(native)
    solver.owned(actor, job).dataset = b'{"fake":true}'
    with pytest.raises(GeometryContractError) as caught:
        solver.dataset(actor, job)
    assert caught.value.code == "CORRUPT_DATASET"
    with pytest.raises(GeometryContractError) as foreign:
        solver.dataset("different-actor", job)
    assert foreign.value.code == "UNKNOWN_RUN"


def test_real_cancellation_retains_no_dataset(native):
    actor, geometry, solver, context, _, _ = native
    current = solver.session(actor).studies[context["study_id"]][0]
    settings = json.loads(replace(current.settings, cells=64, max_iterations=50_000, relative_residual=1e-10).to_json())
    changed = solver.change(actor, context["study_id"], {k: v for k, v in settings.items() if k not in {"schema_version", "content_sha256", "contract_type"}})
    job = solver.submit(actor, geometry, changed["study_id"])["run_id"]
    assert solver.cancel(actor, job)["cancel_requested"] is True
    solver.owned(actor, job).future.result(timeout=10)
    status = solver.status(actor, geometry, job)
    assert status["state"] == "cancelled" and "result" not in status
    assert solver.owned(actor, job).dataset is None


def test_injected_memory_failure_and_retry_releases_queue(native, monkeypatch):
    # Deliberate fault injection, not a native out-of-memory benchmark.
    import simulation.workbench as module
    actual = module.solve
    def fail(*_args, **_kwargs):
        raise MemoryError("P09 test-only solver allocation failure")
    monkeypatch.setattr(module, "solve", fail)
    _, status = run(native)
    assert status["state"] == "failed" and "result" not in status and status["diagnostic"]["action"]
    monkeypatch.setattr(module, "solve", actual)
    _, recovered = run(native)
    assert recovered["state"] == "completed"


def test_actual_source_tamper_refused_before_execution(native):
    actor, geometry, solver, context, job, snapshot = native
    _, candidate = geometry.accepted(actor, job, snapshot)
    path = candidate.directory / "source.brep"
    path.write_bytes(b"P09 test-only tampered native source")
    run_id = solver.submit(actor, geometry, context["study_id"])["run_id"]
    solver.owned(actor, run_id).future.result(timeout=10)
    status = solver.status(actor, geometry, run_id)
    assert status["state"] == "failed" and status["diagnostic"]["code"] and "result" not in status
