"""Actual native workbench guards; optional explicit P08 configuration only."""
import hashlib
import os
import time
from pathlib import Path

import numpy as np
import pytest

from api.ngg_workbench import runtime_config
from systems.contracts.geometry import GeometryContractError
from systems.geometry.workbench import GeometryWorkbench


@pytest.fixture
def manager(tmp_path):
    config = os.environ.get("P08_NATIVE_CONFIG")
    if not config:
        pytest.skip("P08 real workbench requires explicit qualified P08_NATIVE_CONFIG")
    workbench = GeometryWorkbench(tmp_path, runtime_config(Path(config).resolve()))
    yield workbench
    workbench.close()


def test_current_actor_snapshot_exchange_reimport_and_tampering_fail_closed(manager):
    actor = "qualification-a"
    current = manager.context(actor)
    snapshot = current["snapshot"]["content_sha256"]
    job = manager.build(actor, snapshot)["job_id"]
    candidate = manager.owned(actor, job)[1].result(timeout=60)
    state = manager.status(actor, job)
    assert state["fixture_exchange_eligible"] and state["state"] == "accepted"
    filename, data, sha = manager.fixture_bytes(actor, job, snapshot)
    assert filename.endswith(".step") and hashlib.sha256(data).hexdigest() == sha
    vertices = np.frombuffer(manager.preview(actor, job, snapshot), dtype="<f4")
    assert len(vertices) % 9 == 0 and np.isfinite(vertices).all()
    measurement = manager.measure(actor, job, snapshot, [0, 1])
    assert measurement["distance_m"] >= 0 and not measurement["physical_validation"]
    for operation in (lambda: manager.status("qualification-b", job), lambda: manager.activate("qualification-b", snapshot),
                      lambda: manager.measure(actor, job, snapshot, [10**9, 0]), lambda: manager.reimport(actor, job, snapshot, data + b"x")):
        with pytest.raises(GeometryContractError):
            operation()
    imported = manager.reimport(actor, job, snapshot, data)["reimport_id"]
    deadline = time.monotonic() + 60
    while (result := manager.reimport_status(actor, imported))["state"] != "completed":
        assert time.monotonic() < deadline
        time.sleep(.05)
    assert result["result"]["pass"] and result["result"]["artifact_sha256"] == sha
    assert not result["result"]["published"] and not candidate.record.published_artifacts
    newer = manager.change(actor, snapshot, {"operation": "union", "backend": "occt", "voxel_m": .0005})
    assert newer["snapshot"]["content_sha256"] != snapshot
    with pytest.raises(GeometryContractError, match="snapshot"):
        manager.fixture_bytes(actor, job, snapshot)
    manager.activate(actor, snapshot)
    assert manager.status(actor, job)["fixture_exchange_eligible"]
    artifact = candidate.directory / "export.step"
    artifact.write_bytes(data + b"tampered")
    assert not manager.status(actor, job)["fixture_exchange_eligible"]
    with pytest.raises(GeometryContractError):
        manager.fixture_bytes(actor, job, snapshot)
    assert manager.session(actor).previews  # Cached preview may not bypass byte-integrity guard.
    with pytest.raises(GeometryContractError):
        manager.preview(actor, job, snapshot)


def test_revision_bounds_no_client_radius_or_unsafe_activation(manager):
    current = manager.context("qualification-c")
    snapshot = current["snapshot"]["content_sha256"]
    with pytest.raises(GeometryContractError):
        manager.change("qualification-c", "wrong", current["settings"])
    with pytest.raises(GeometryContractError):
        manager.change("qualification-c", snapshot, {**current["settings"], "radius_m": .1})
    for _ in range(15):
        current = manager.change("qualification-c", current["snapshot"]["content_sha256"], current["settings"])
    with pytest.raises(GeometryContractError):
        manager.change("qualification-c", current["snapshot"]["content_sha256"], current["settings"])
    assert len(manager.session("qualification-c").revisions) == 16
