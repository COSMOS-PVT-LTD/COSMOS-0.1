"""SIGKILL a real accepted native fixture before durable terminal publication."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.persistence.application_authority import ApplicationAuthority
from systems.geometry.authority import source_payload
from systems.geometry.workbench import GeometryWorkbench
from systems.persistence.job_repository import JobState
from systems.projects.authority import Head, Principal

CHILD = """
import json, os, signal, sys
from pathlib import Path
from infrastructure.geometry import WorkerSupervisor
from infrastructure.persistence.application_authority import ApplicationAuthority
from plugins.geometry.adapters import OCCTAdapter, PicoGKAdapter
from systems.contracts.geometry import GeometryBuildEvent, BuildState
from systems.geometry.authority import ManagedGeometry
from systems.geometry.service import GeometryBuildService
from systems.projects.authority import Principal
from tests.integration_tests.geometry.conftest import command
root, project, config_path, backend, marker, candidate_dir = sys.argv[1:]
actor = Principal('USR-native-crash','ENGINEER')
config = json.loads(Path(config_path).read_text())
app = ApplicationAuthority(Path(root), enabled=True)
supervisor = WorkerSupervisor(timeout_s=45)
service = GeometryBuildService((OCCTAdapter if backend=='occt' else PicoGKAdapter)(command(config,backend),supervisor,enabled=True),
    Path(candidate_dir),step_reader=command(config,'step_reader') if backend=='occt' else None)
coordinator = ManagedGeometry(app.repository,app.jobs,lambda:{backend:service},lambda _:actor)
original = app.jobs.append_stage
def append(job_id,payload):
    receipt = original(job_id,payload)
    if GeometryBuildEvent.from_json(payload.data.decode()).state is BuildState.ACCEPTED:
        Path(marker).write_text(job_id)
        os.kill(os.getpid(),signal.SIGKILL)
    return receipt
app.jobs.append_stage = append
source = app.repository.get_snapshot(actor,project,domain='geometry-fixture',object_id='fixture')
coordinator.start(actor,source,operation_id='native-crash',request_hash='5'*64)
# Shutdown joins the running coordination; SIGKILL occurs in its accepted sink,
# after the native process and independent QA, before terminal metadata returns.
coordinator.pool.shutdown(wait=True)
raise RuntimeError('Expected actual accepted-stage SIGKILL did not occur')
"""


@pytest.mark.skipif(os.name != "posix", reason="Qualified POSIX coordinator boundary")
@pytest.mark.parametrize("backend", ["occt", "picogk"])
def test_actual_native_acceptance_then_host_kill_never_publishes(native_config, tmp_path, backend):
    actor = Principal("USR-native-crash", "ENGINEER")
    root, candidates = tmp_path / "authority", tmp_path / "candidates"
    candidates.mkdir()
    app = ApplicationAuthority(root, enabled=True)
    project = app.repository.create_project(actor, title="Actual native host crash fixture", mission="Software only", operation_id="project")
    revision = GeometryWorkbench.revision({"operation": "difference", "backend": backend, "voxel_m": .0005})
    app.repository.save_snapshot(actor, project.project_id, domain="geometry-fixture", object_id="fixture", input_revision=0,
        payload=source_payload(revision), expected=Head.absent(), operation_id="input")
    app.close()
    marker = tmp_path / "accepted-job"
    result = subprocess.run([sys.executable, "-c", CHILD, str(root), project.project_id,
        os.environ["P07_NATIVE_CONFIG"], backend, str(marker), str(candidates)], capture_output=True, timeout=90, check=False)
    assert result.returncode == -signal.SIGKILL, result.stderr.decode()[-2000:]
    recovered = ApplicationAuthority(root, enabled=True)
    try:
        job = recovered.jobs.get(actor, project.project_id, marker.read_text())
        assert job.state is JobState.INTERRUPTED and not job.selected and not job.blobs
        stages = recovered.jobs.list_stages(actor, project.project_id, job.job_id)
        assert stages[-1].state == "accepted"
        assert json.loads(recovered.jobs.stage_source(actor, project.project_id, job.job_id, stages[-1].sequence))["state"] == "accepted"
        native_files = list(candidates.glob("*/source.brep" if backend == "occt" else "*/source.vdb"))
        assert len(native_files) == 1  # Existing native output is not an authoritative result.
        evidence = Path(native_config["evidence_directory"]) / "crash"
        evidence.mkdir(exist_ok=True)
        (evidence / f"{backend}.json").write_text(json.dumps({"backend": backend, "actual_host_signal": "SIGKILL",
            "last_native_stage": stages[-1].state, "recovered_state": job.state.value, "retained_stages": len(stages),
            "selected": job.selected, "durable_exchange_blobs": len(job.blobs), "native_source_exists": True,
            "software_only": True, "physical_validation": False}, indent=2) + "\n")
    finally:
        recovered.close()
