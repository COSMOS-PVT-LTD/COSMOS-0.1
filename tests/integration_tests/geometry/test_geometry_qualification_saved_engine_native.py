"""Explicit immutable saved-engine diagnostic, not an intended-use acceptance."""

import json
import os
from hashlib import sha256
from pathlib import Path

import pytest

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from plugins.geometry.component_adapter import ComponentAdapter
from systems.contracts.geometry import BuildState, DesignSnapshot, GeometryFeatureGraph
from systems.geometry.component_model import from_contracts
from systems.geometry.component_qa import ComponentBuildService, ComponentQALimits
from systems.geometry.component_reference import ComponentReference
from systems.geometry.component_workspace import COMPONENT_VERIFICATION_OUTPUT_BYTES
from tests.fixtures.component_geometry import qa_spec
from tests.fixtures.geometry_qualification_families import (
    area_reference,
    critical_witnesses,
)
from tests.integration_tests.geometry.test_component_native import commands, request_for


def test_exact_saved_engine_nominal_areas_dimensions_semantics_and_reimport(
    tmp_path, record_property
):
    source = os.environ.get("R08_ENGINE_CAPTURE")
    checksum = os.environ.get("R08_ENGINE_CAPTURE_SHA256")
    if not source or not checksum:
        pytest.skip("Explicit immutable engine capture and expected checksum required")
    path = Path(source)
    assert path.is_absolute() and path.is_file() and not path.is_symlink()
    assert path.stat().st_size <= 2 * 1024**2
    raw = path.read_bytes()
    assert sha256(raw).hexdigest() == checksum
    captured = json.loads(raw)
    assert (
        sha256(captured["model_canonical_json"].encode()).hexdigest()
        == captured["model_sha256"]
    )
    model = json.loads(captured["model_canonical_json"])
    plan = from_contracts(
        DesignSnapshot.from_json(model["snapshot_json"]),
        GeometryFeatureGraph.from_json(model["graph_json"]),
    )
    # Independent formulas/nominal witnesses are declared before native work.
    references = [
        {
            "part_id": p.part_id,
            "area_m2": area_reference(p),
            "nominal_source_witnesses": critical_witnesses(plan, p),
        }
        for p in plan.parts
    ]
    worker = commands()
    reader = WorkerCommand(
        (
            worker.argv[0],
            str(Path(worker.argv[1]).with_name("component_step_reader.py")),
        ),
        worker.environment,
    )
    with WorkerSupervisor(
        timeout_s=120, stdout_limit=COMPONENT_VERIFICATION_OUTPUT_BYTES
    ) as supervisor:
        service = ComponentBuildService(
            ComponentAdapter("occt", worker, supervisor, enabled=True),
            tmp_path,
            step_reader=reader,
            limits=ComponentQALimits.from_spec(qa_spec()),
        )
        try:
            _, future = service.submit(
                request_for(plan), plan.snapshot, plan.graph, ComponentReference(plan)
            )
            result = future.result(timeout=240)
            evidence = json.loads(result.evidence_json)
            assert result.record.state is BuildState.ACCEPTED, {
                k: evidence.get(k)
                for k in ("diagnostic", "process", "qa-stl", "qa-step")
            }
            assert (
                evidence["qa-step"]["pass"]
                and evidence["qa-step"]["semantic_mapping_pass"]
                and evidence["qa-stl"]["topology_pass"]
            )
            for reference, actual in zip(
                references, evidence["worker_observations"]["parts"], strict=True
            ):
                assert reference["part_id"] == actual["part_id"]
                reference["occt_area_m2"] = sum(f["area_m2"] for f in actual["faces"])
                assert reference["occt_area_m2"] == pytest.approx(
                    reference["area_m2"], rel=1e-8
                )
        finally:
            service.close()
    record_property(
        "r08_saved_engine_nominal_diagnostic",
        json.dumps(
            {
                "capture_path": str(path),
                "capture_sha256": checksum,
                "model_commit_id": captured["model_commit_id"],
                "model_sha256": captured["model_sha256"],
                "part_count": len(plan.parts),
                "parts": references,
                "record_json": result.record.to_json(),
                "evidence": evidence,
                "scope": "INDEPENDENT_NOMINAL_REFERENCE_CHECK_ONLY",
                "engine_intended_use_policy": "NOT_INSTALLED",
                "engineering_acceptance": "NOT_PERFORMED",
                "whole_engine_implicit_refinement": "NOT_PERFORMED",
                "physical_validation": "NOT_PERFORMED",
            }
        ),
    )
