"""Actual SIGKILL around durable metadata publication, not native/power-loss QA."""
from __future__ import annotations

import os
import signal
import subprocess
import sys

import pytest

from infrastructure.persistence.application_authority import ApplicationAuthority
from systems.geometry.authority import source_payload
from systems.geometry.workbench import GeometryWorkbench
from systems.persistence.job_repository import JobState
from systems.persistence.project_repository import RecordPayload
from systems.projects.authority import Head, Principal

CHILD = """
import os, signal, sys
from pathlib import Path
from hashlib import sha256
from infrastructure.persistence.application_authority import ApplicationAuthority
from infrastructure.persistence.durable_jobs import message
from systems.persistence.job_repository import BlobAttachment, JobState
from systems.projects.authority import Principal
root, project, boundary, marker = sys.argv[1:]
actor = Principal('USR-owner','ENGINEER')
app = ApplicationAuthority(Path(root), enabled=True)
source = app.repository.get_snapshot(actor, project, domain='geometry-fixture', object_id='fixture')
job = app.jobs.admit(actor, source, operation_id='child-admit', request_hash='1'*64)
Path(marker).write_text(job.job_id)
app.jobs.advance(job.job_id, JobState.RUNNING, message('RUNNING'))
data = b'synthetic attachment before SIGKILL'
original = app.repository.files.install_blob
def install(value, digest):
    original(value, digest)
    if boundary == 'installed-before-commit' and value == data:
        os.kill(os.getpid(), signal.SIGKILL)
app.repository.files.install_blob = install
app.jobs.advance(job.job_id, JobState.COMPLETED, message('DONE'), actor=actor,
    attachments=(BlobAttachment('export.step',data,sha256(data).hexdigest(),'artifact'),))
os.kill(os.getpid(), signal.SIGKILL)
"""


@pytest.mark.skipif(os.name != "posix", reason="Existing POSIX coordinator qualification only")
@pytest.mark.parametrize("boundary", ["installed-before-commit", "committed-before-ack"])
def test_sigkill_never_publishes_partial_and_preserves_committed_receipt(tmp_path, boundary):
    root = tmp_path / "app"
    actor = Principal("USR-owner", "ENGINEER")
    app = ApplicationAuthority(root, enabled=True)
    project = app.repository.create_project(actor, title="SIGKILL software fixture", mission="No physical evidence", operation_id="create")
    app.repository.save_snapshot(actor, project.project_id, domain="geometry-fixture", object_id="fixture", input_revision=0,
        payload=RecordPayload(b'{"synthetic":true}', "test.input.v1"), expected=Head.absent(), operation_id="input")
    app.close()
    marker = tmp_path / "attempt-id"
    result = subprocess.run([sys.executable, "-c", CHILD, str(root), project.project_id, boundary, str(marker)],
        capture_output=True, timeout=15, check=False)
    assert result.returncode == -signal.SIGKILL, result.stderr.decode()[:1000]
    recovered = ApplicationAuthority(root, enabled=True)
    try:
        job = recovered.jobs.get(actor, project.project_id, marker.read_text())
        if boundary == "installed-before-commit":
            assert job.state is JobState.INTERRUPTED and not job.blobs and not job.selected
            # Installed unreferenced bytes are retained, never silently purged or claimed as output.
            assert len(list(recovered.repository.files.blobs.iterdir())) > 3
        else:
            assert job.state is JobState.COMPLETED and job.selected and job.current_input
            assert recovered.jobs.blob(actor, project.project_id, job.job_id, "export.step") == b"synthetic attachment before SIGKILL"
            replay = recovered.jobs.admit(actor, recovered.repository.get_snapshot(actor, project.project_id, domain="geometry-fixture", object_id="fixture"),
                operation_id="child-admit", request_hash="1"*64)
            assert replay.job_id == job.job_id
    finally:
        recovered.close()


STAGE_CHILD = """
import os, signal, sys
from pathlib import Path
from infrastructure.persistence.application_authority import ApplicationAuthority
from infrastructure.persistence.durable_jobs import message
from systems.contracts.geometry import BuildState, GeometryBuildEvent
from systems.geometry.authority import decode_source
from systems.persistence.job_repository import JobState
from systems.persistence.project_repository import RecordPayload
from systems.projects.authority import Principal
root, project, boundary, marker = sys.argv[1:]
actor = Principal('USR-owner','ENGINEER')
app = ApplicationAuthority(Path(root), enabled=True)
source = app.repository.get_snapshot(actor, project, domain='geometry-fixture', object_id='fixture')
revision = decode_source(source)
job = app.jobs.admit(actor, source, operation_id='stage-child', request_hash='4'*64)
Path(marker).write_text(job.job_id)
app.jobs.advance(job.job_id, JobState.RUNNING, message('RUNNING'))
stage = GeometryBuildEvent('native-stage-child',0,'2026-10-18T00:00:00+00:00',BuildState.DRAFT,'draft',None,None,
    'Synthetic stage SIGKILL boundary only',(),(),revision.request.correlation_id)
payload = RecordPayload(stage.to_json().encode(),'cosmos.geometry-stage.v1','p07-software-fixtures')
original = app.repository.files.install_blob
def install(value,digest):
    original(value,digest)
    if boundary == 'stage-installed-before-commit' and value == payload.data:
        os.kill(os.getpid(),signal.SIGKILL)
app.repository.files.install_blob = install
app.jobs.append_stage(job.job_id,payload)
os.kill(os.getpid(),signal.SIGKILL)
"""


@pytest.mark.skipif(os.name != "posix", reason="Existing POSIX coordinator qualification only")
@pytest.mark.parametrize("boundary", ["stage-installed-before-commit", "stage-committed-before-ack"])
def test_sigkill_preserves_only_committed_native_stage_prefix(tmp_path, boundary):
    root = tmp_path / "app"
    actor = Principal("USR-owner", "ENGINEER")
    app = ApplicationAuthority(root, enabled=True)
    project = app.repository.create_project(actor, title="Stage SIGKILL software fixture", mission="No native/hardware claim", operation_id="create")
    revision = GeometryWorkbench.revision({"operation": "sphere", "backend": "occt", "voxel_m": .0005})
    app.repository.save_snapshot(actor, project.project_id, domain="geometry-fixture", object_id="fixture", input_revision=0,
        payload=source_payload(revision), expected=Head.absent(), operation_id="input")
    app.close()
    marker = tmp_path / "attempt-id"
    result = subprocess.run([sys.executable, "-c", STAGE_CHILD, str(root), project.project_id, boundary, str(marker)],
        capture_output=True, timeout=15, check=False)
    assert result.returncode == -signal.SIGKILL, result.stderr.decode()[:1000]
    recovered = ApplicationAuthority(root, enabled=True)
    try:
        job = recovered.jobs.get(actor, project.project_id, marker.read_text())
        assert job.state is JobState.INTERRUPTED and not job.blobs and not job.selected
        stages = recovered.jobs.list_stages(actor, project.project_id, job.job_id)
        assert len(stages) == (0 if boundary == "stage-installed-before-commit" else 1)
        if stages:
            raw = recovered.jobs.stage_source(actor, project.project_id, job.job_id, 0)
            assert b'Synthetic stage SIGKILL boundary only' in raw
    finally:
        recovered.close()
