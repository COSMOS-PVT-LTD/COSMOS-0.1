"""Actual isolated native geometry, not mocks and not physical validation."""
import hashlib
import json
import time
from dataclasses import replace
from pathlib import Path

import pytest

from infrastructure.geometry import WorkerSupervisor
from plugins.geometry.adapters import OCCTAdapter, PicoGKAdapter
from systems.contracts.geometry import BuildState, OutputFormat
from systems.geometry.qa import FixtureReference, audit_mesh
from systems.geometry.service import GeometryBuildService
from tests.fixtures.ngg_cases import case

from .conftest import command

SPHERICAL = ("sphere", "union", "difference", "intersection", "self_union")
RESOLUTIONS = (.001, .0005, .00025)


def retain(config, label, candidate):
    directory = Path(config["evidence_directory"]) / "fixtures" / label
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "record.json").write_text(candidate.record.to_json() + "\n")
    (directory / "qa.json").write_text(candidate.evidence_json + "\n")
    # Only exact known output names, including rejected private forensic candidates.
    for name in ("source.vdb", "source.brep", "export.stl", "export.step", "export-conditioned.stl"):
        path = candidate.directory / name
        if path.is_file() and not path.is_symlink():
            (directory / name).write_bytes(path.read_bytes())


@pytest.mark.parametrize("operation", SPHERICAL)
@pytest.mark.parametrize("voxel", RESOLUTIONS)
def test_picogk_three_resolution_conditioned_qa(native_config, tmp_path, operation, voxel):
    with WorkerSupervisor(timeout_s=45) as supervisor:
        service = GeometryBuildService(PicoGKAdapter(command(native_config, "picogk"), supervisor, enabled=True), tmp_path)
        s, g, r = case(operation, voxel=voxel)
        _, future = service.submit(r, s, g, FixtureReference(operation), conditioning_profile="exact_zero_faces_v1")
        candidate = future.result(timeout=60)
        retain(native_config, f"pico-{operation}-{voxel}", candidate)
        qa = json.loads(candidate.evidence_json)
        expected = BuildState.REJECTED if operation == "intersection" and voxel == .001 else BuildState.ACCEPTED
        assert candidate.record.state is expected, qa
        assert not candidate.record.published_artifacts
        assert qa["worker_observations"]["actual_voxel_m"] == voxel
        assert qa["conditioning"]["surviving_vertices_identical"] and not qa["conditioning"]["voxel_refinement"]
        if expected is BuildState.ACCEPTED:
            assert qa["qa-stl"]["pass"] and service.inspect(candidate, s, g)["current"]
            assert service.inspect(candidate, s, g)["export_eligibility"] == (False, ("NOT_PUBLISHED",))
            candidate_file = candidate.directory / "export-conditioned.stl"
            original = candidate_file.read_bytes(); candidate_file.write_bytes(original + b"tampered")
            assert not service.inspect(candidate, s, g)["byte_integrity"]
            candidate_file.write_bytes(original)
        else:
            assert qa["qa-stl"]["topology_pass"] and not qa["qa-stl"]["dimensions_pass"] and not candidate.record.artifacts
        service.close()


@pytest.mark.parametrize("voxel", RESOLUTIONS)
def test_picogk_raw_subtraction_remains_refused(native_config, tmp_path, voxel):
    with WorkerSupervisor() as supervisor:
        service = GeometryBuildService(PicoGKAdapter(command(native_config, "picogk"), supervisor, enabled=True), tmp_path)
        s, g, r = case("difference", voxel=voxel)
        _, future = service.submit(r, s, g, FixtureReference("difference"))
        candidate = future.result(timeout=60)
        retain(native_config, f"pico-raw-difference-{voxel}", candidate)
        qa = json.loads(candidate.evidence_json)["qa-stl"]
        assert candidate.record.state is BuildState.REJECTED and not candidate.record.artifacts
        assert not qa["topology_pass"] and qa["degenerate_faces"] > 0
        service.close()


@pytest.mark.parametrize("backend", ["picogk", "occt"])
@pytest.mark.parametrize("operation", ["self_difference", "disjoint_intersection"])
def test_native_empty_geometry_rejected_without_files(native_config, tmp_path, backend, operation):
    with WorkerSupervisor() as supervisor:
        adapter = (PicoGKAdapter if backend == "picogk" else OCCTAdapter)(command(native_config, backend), supervisor, enabled=True)
        service = GeometryBuildService(adapter, tmp_path)
        s, g, r = case(operation, backend=backend)
        _, future = service.submit(r, s, g, FixtureReference("sphere"))
        candidate = future.result(timeout=60)
        retain(native_config, backend + "-empty-" + operation, candidate)
        assert candidate.record.state is BuildState.FAILED and candidate.record.events[-1].code == "EMPTY_GEOMETRY"
        assert not candidate.record.artifacts and not list(candidate.directory.iterdir())
        service.close()


@pytest.mark.parametrize("operation", SPHERICAL + ("box", "cylinder"))
def test_occt_step_independent_tool_reimport(native_config, tmp_path, operation):
    with WorkerSupervisor() as supervisor:
        service = GeometryBuildService(OCCTAdapter(command(native_config, "occt"), supervisor, enabled=True), tmp_path,
                                       step_reader=command(native_config, "step_reader"))
        s, g, r = case(operation, backend="occt")
        _, future = service.submit(r, s, g, FixtureReference(operation))
        candidate = future.result(timeout=60)
        retain(native_config, "occt-step-" + operation, candidate)
        qa = json.loads(candidate.evidence_json)
        assert candidate.record.state is BuildState.ACCEPTED, qa
        assert qa["qa-step"]["pass"] and qa["qa-step"]["file_units"] == "m"
        assert not qa["qa-step"]["reader_kernel_independence"] and not candidate.record.published_artifacts
        service.close()


def test_occt_step_and_stl_representation_aware_export(native_config, tmp_path):
    with WorkerSupervisor() as supervisor:
        service = GeometryBuildService(OCCTAdapter(command(native_config, "occt"), supervisor, enabled=True), tmp_path,
                                       step_reader=command(native_config, "step_reader"))
        s, g, r = case("sphere", backend="occt", formats=(OutputFormat.STEP, OutputFormat.STL))
        _, future = service.submit(r, s, g, FixtureReference("sphere"))
        candidate = future.result(timeout=60)
        retain(native_config, "occt-both-sphere", candidate)
        assert candidate.record.state is BuildState.ACCEPTED, candidate.evidence_json
        assert {a.output_format for a in candidate.record.artifacts} == {OutputFormat.STEP, OutputFormat.STL}
        assert all(a.representation.value == "analytic_brep" for a in candidate.record.artifacts)
        qa = audit_mesh(candidate.directory / "export.stl", FixtureReference("sphere"), voxel_m=None, export_tolerance_m=1e-6)
        assert qa["pass"]  # Source analytic, exported STL explicitly tessellated.
        service.close()


def test_native_worker_health_exact_wire_hashes_and_cancel(native_config, tmp_path):
    s, g, r = case("union", voxel=.00025)
    # Larger explicit bounded native request, not a hidden fixture refinement.
    s = replace(s, parameters_si=tuple(replace(p, value_si=.025) if p.name.endswith(".radius") else p for p in s.parameters_si))
    g = replace(g, snapshot_id=s.snapshot_id)
    r = replace(r, snapshot_id=s.snapshot_id, feature_graph_sha256=g.content_sha256)
    with WorkerSupervisor() as supervisor:
        adapter = PicoGKAdapter(command(native_config, "picogk"), supervisor, enabled=True)
        health = adapter.health("health", r, s, g, tmp_path).result(timeout=10)
        assert health.code == "OK"
        event = json.loads(health.stdout)
        assert event["wire_sha256"] == {"request": hashlib.sha256(r.to_json().encode()).hexdigest(),
                                        "snapshot": hashlib.sha256(s.to_json().encode()).hexdigest(),
                                        "graph": hashlib.sha256(g.to_json().encode()).hexdigest()}
        future = adapter.build("native-cancel", r, s, g, tmp_path)
        # Actual launched native-session cancellation; no simulator or sleep-worker.
        time.sleep(.3)
        assert adapter.cancel("native-cancel")
        result = future.result(timeout=5)
        assert result.code == "CANCELLED" and result.pid is not None and b'"started"' in result.stdout
        evidence = Path(native_config["evidence_directory"]) / "native-cancel.json"
        evidence.write_text(json.dumps({"code": result.code, "pid": result.pid, "exit_code": result.exit_code,
                                       "observed_rss_bytes": result.maximum_rss_bytes, "stdout": result.stdout.decode(),
                                       "elapsed_s": result.elapsed_s, "scope": "after started event, native session; not certified mid-operation callback"}, indent=2) + "\n")
