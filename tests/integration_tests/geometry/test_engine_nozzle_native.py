"""Explicit optional pinned native engine-nozzle software qualification."""

import json
import os
import time
from pathlib import Path

import pytest

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from plugins.geometry.nozzle_adapter import NozzleAdapter
from plugins.geometry.nozzle_protocol import profile
from systems.contracts.geometry import BuildState
from systems.geometry.nozzle_qa import NozzleBuildService, NozzleQALimits
from systems.geometry.nozzle_reference import NozzleReference
from tests.fixtures.nozzle_geometry import case, qa_spec


def commands():
    path = os.environ.get("R07_NATIVE_CONFIG")
    if not path:
        pytest.skip("R07 explicit pinned local native runtime required; no autodetection")
    cfg = json.loads(Path(path).read_text())
    root = Path(__file__).resolve().parents[3]
    env = tuple(cfg["occt"]["environment"].items())
    return WorkerCommand((cfg["occt"]["argv"][0], str(root / "plugins/geometry/workers/nozzle_worker.py")), env), WorkerCommand((cfg["step_reader"]["argv"][0], str(root / "plugins/geometry/workers/nozzle_step_reader.py")), env)


@pytest.mark.parametrize("points", [((0., .01), (.04, .02)), ((0., .01), (.01, .012), (.025, .019), (.04, .024))])
def test_actual_nozzle_step_stl_analytic_volume_topology_reimport(tmp_path, points):
    worker, reader = commands()
    with WorkerSupervisor(timeout_s=60) as supervisor:
        service = NozzleBuildService(NozzleAdapter("occt", worker, supervisor, enabled=True), tmp_path, step_reader=reader, limits=NozzleQALimits.from_spec(qa_spec()))
        try:
            s, g, r = case(points)
            _, future = service.submit(r, s, g, NozzleReference(profile(s, g)))
            candidate = future.result(timeout=120)
            assert candidate.record.state is BuildState.ACCEPTED, candidate.evidence_json
            evidence = json.loads(candidate.evidence_json)
            assert evidence["qa-stl"]["euler_characteristic"] == 0
            assert evidence["qa-stl"]["pass"] and evidence["qa-step"]["pass"]
            assert len(candidate.record.artifacts) == 2 and not candidate.record.published_artifacts
        finally:
            service.close()


def test_actual_nozzle_health_crash_and_timeout_never_fall_back(tmp_path):
    worker, reader = commands()
    s, g, r = case()
    with WorkerSupervisor(timeout_s=60) as supervisor:
        adapter = NozzleAdapter("occt", worker, supervisor, enabled=True)
        health = adapter.health("health", r, s, g, tmp_path).result(timeout=10)
        assert health.code == "OK" and json.loads(health.stdout)["native_version"] == "7.8.1.1"
        broken = WorkerCommand((worker.argv[0], str(tmp_path / "missing-nozzle-worker.py")), worker.environment)
        service = NozzleBuildService(NozzleAdapter("occt", broken, supervisor, enabled=True), tmp_path, step_reader=reader, limits=NozzleQALimits.from_spec(qa_spec()))
        try:
            _, future = service.submit(r, s, g, NozzleReference(profile(s, g)))
            failed = future.result(timeout=10)
            assert failed.record.state is BuildState.FAILED and not failed.record.artifacts
        finally:
            service.close()
    with WorkerSupervisor(timeout_s=.05) as supervisor:
        result = NozzleAdapter("occt", worker, supervisor, enabled=True).health("timeout", r, s, g, tmp_path).result(timeout=5)
        assert result.code == "TIMEOUT" and result.pid is not None


def test_actual_launched_nozzle_process_cancel_retains_no_accepted_artifact(tmp_path):
    worker, _ = commands()
    s, g, r = case()
    with WorkerSupervisor(timeout_s=60) as supervisor:
        adapter = NozzleAdapter("occt", worker, supervisor, enabled=True)
        future = adapter.build("cancel", r, s, g, tmp_path)
        time.sleep(.08)  # Launched-session boundary, not a claimed in-kernel callback.
        assert adapter.cancel("cancel")
        result = future.result(timeout=5)
        assert result.code == "CANCELLED" and result.pid is not None


def test_three_declared_tessellation_levels_refine_against_same_exact_profile(tmp_path):
    worker, reader = commands()
    errors, counts = [], []
    with WorkerSupervisor(timeout_s=60) as supervisor:
        limits = qa_spec()
        limits["surface_distance"]["value"] = 1e-4
        service = NozzleBuildService(NozzleAdapter("occt", worker, supervisor, enabled=True), tmp_path, step_reader=reader, limits=NozzleQALimits.from_spec(limits))
        try:
            for h in (1e-4, 2e-5, 4e-6):
                s, g, r = case(tolerance=h)
                _, future = service.submit(r, s, g, NozzleReference(profile(s, g)))
                candidate = future.result(timeout=120)
                assert candidate.record.state is BuildState.ACCEPTED, candidate.evidence_json
                evidence = json.loads(candidate.evidence_json)
                errors.append(evidence["qa-stl"]["relative_volume_error"])
                counts.append(evidence["qa-stl"]["triangle_count"])
            assert errors[-1] < errors[0] and counts[-1] > counts[0]
        finally:
            service.close()
