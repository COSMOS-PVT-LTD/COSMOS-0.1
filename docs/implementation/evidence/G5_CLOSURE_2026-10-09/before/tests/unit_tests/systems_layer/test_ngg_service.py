import sys
import time
from dataclasses import replace

import pytest

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from plugins.geometry.adapters import PicoGKAdapter
from systems.contracts.geometry import BuildState, GeometryContractError, Representation
from systems.geometry.qa import FixtureReference
from systems.geometry.service import GeometryBuildService
from tests.fixtures.ngg_cases import case


def test_disabled_service_uses_p06_terminal_record_and_never_publishes(tmp_path):
    with WorkerSupervisor() as supervisor:
        service = GeometryBuildService(PicoGKAdapter(WorkerCommand((sys.executable, "-c", "raise RuntimeError('must not run')")), supervisor), tmp_path)
        s, g, r = case()
        _, future = service.submit(r, s, g, FixtureReference("sphere"))
        candidate = future.result(timeout=2)
        assert candidate.record.state is BuildState.REJECTED and candidate.record.events[-1].code == "NGG_DISABLED"
        assert not candidate.record.artifacts and not candidate.record.published_artifacts
        assert service.inspect(candidate, s, g)["export_eligibility"] == (False, ("NOT_PUBLISHED",))
        with pytest.raises(GeometryContractError):
            service.export(candidate)
        service.close()
        with pytest.raises(GeometryContractError):
            service.submit(r, s, g, FixtureReference("sphere"))


@pytest.mark.parametrize("defect", ["frame", "representation", "stale", "project", "conditioning"])
def test_service_refuses_invalid_inputs_before_admission(tmp_path, defect):
    with WorkerSupervisor() as supervisor:
        service = GeometryBuildService(PicoGKAdapter(WorkerCommand((sys.executable, "-c", "pass")), supervisor), tmp_path)
        s, g, r = case()
        profile = "raw"
        if defect == "frame":
            r = replace(r, frame_id="missing")
        elif defect == "representation":
            r = replace(r, representation=Representation.TESSELLATED_SURFACE, approximation_profile="surface_mesh", voxel_resolution_m=None)
        elif defect == "stale":
            r = replace(r, feature_graph_sha256="a"*64)
        elif defect == "project":
            s = replace(s, project_id="real-engine")
        else:
            profile = "silent_refinement"
        with pytest.raises(GeometryContractError):
            service.submit(r, s, g, FixtureReference("sphere"), conditioning_profile=profile)
        assert not list(tmp_path.iterdir())
        service.close()


def test_real_worker_crash_returns_failed_record_without_candidate(tmp_path):
    with WorkerSupervisor() as supervisor:
        service = GeometryBuildService(PicoGKAdapter(WorkerCommand((sys.executable, "-c", "raise SystemExit(7)")), supervisor, enabled=True), tmp_path)
        s, g, r = case()
        _, future = service.submit(r, s, g, FixtureReference("sphere"))
        candidate = future.result(timeout=3)
        assert candidate.record.state is BuildState.FAILED and candidate.record.events[-1].code == "WORKER_CRASH"
        assert not candidate.record.artifacts
        service.close()


def test_bounded_coordinator_queue_and_running_queued_cancellation(tmp_path):
    with WorkerSupervisor(timeout_s=5) as supervisor:
        service = GeometryBuildService(PicoGKAdapter(WorkerCommand((sys.executable, "-c", "import time;time.sleep(4)")), supervisor, enabled=True), tmp_path)
        s, g, r = case()
        jobs = [service.submit(r, s, g, FixtureReference("sphere")) for _ in range(3)]
        time.sleep(.05)
        with pytest.raises(GeometryContractError) as error:
            service.submit(r, s, g, FixtureReference("sphere"))
        assert error.value.code == "QUEUE_FULL"
        assert service.cancel(jobs[2][0]) and service.cancel(jobs[0][0]) and service.cancel(jobs[1][0])
        for _, future in jobs:
            candidate = future.result(timeout=3)
            assert candidate.record.state is BuildState.CANCELLED and not candidate.record.artifacts
            assert not list(candidate.directory.iterdir())
        assert not service.cancel("missing")
        service.close()
