"""Real native QA breadth. Manufactured cases, never target-engine approval."""

import json
import threading
from hashlib import sha256
from pathlib import Path

import pytest

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from plugins.geometry.component_adapter import ComponentAdapter
from plugins.geometry.pico_components import PicoComponentAdapter, field_graph
from systems.contracts.geometry import BuildState
from systems.geometry.component_qa import ComponentBuildService, ComponentQALimits
from systems.geometry.component_reference import ComponentReference
from systems.geometry.pico_component_builds import (
    PicoBuildService,
    PicoLimits,
    PicoReference,
)
from systems.geometry.qualification import QualificationRuntime
from tests.fixtures.component_geometry import qa_spec
from tests.fixtures.geometry_qualification_families import (
    FAMILIES,
    family_plan,
    family_policy,
)
from tests.integration_tests.geometry.test_component_native import commands, request_for
from tests.integration_tests.geometry.test_pico_components_native import (
    command as pico_command,
)
from tests.unit_tests.systems_layer.test_pico_components import (
    qa,
)
from tests.unit_tests.systems_layer.test_pico_components import (
    request_for as pico_request,
)


@pytest.mark.parametrize("kind", FAMILIES)
def test_r08_real_family_three_grids_independent_area_critical_features_and_reimport(
    tmp_path, record_property, kind
):
    plan = family_plan(kind)
    policy = family_policy(plan)  # Predeclared BEFORE all native generation.
    policy_bytes = json.dumps(policy, sort_keys=True, allow_nan=False).encode()
    worker = commands()
    reader = WorkerCommand(
        (
            worker.argv[0],
            str(Path(worker.argv[1]).with_name("component_step_reader.py")),
        ),
        worker.environment,
    )
    pico_worker = pico_command()
    root = Path(__file__).resolve().parents[3]
    runtime = QualificationRuntime(
        lambda: {"python": str(root / ".venv-release-p12/bin/python")}
    )
    campaign = []
    (tmp_path / "analytic").mkdir()
    with WorkerSupervisor(timeout_s=120) as supervisor:
        analytic_service = ComponentBuildService(
            ComponentAdapter("occt", worker, supervisor, enabled=True),
            tmp_path / "analytic",
            step_reader=reader,
            limits=ComponentQALimits.from_spec(qa_spec()),
        )
        try:
            _, future = analytic_service.submit(
                request_for(plan), plan.snapshot, plan.graph, ComponentReference(plan)
            )
            analytic = future.result(timeout=240)
            assert analytic.record.state is BuildState.ACCEPTED, analytic.evidence_json
            evidence = json.loads(analytic.evidence_json)
            assert (
                evidence["qa-step"]["pass"]
                and evidence["qa-step"]["semantic_mapping_pass"]
            )
            # The BREP's exact area independently checks the closed-form reference,
            # separately from approximate tessellation/voxel acceptance limits.
            for limits, actual in zip(
                policy["parts"], evidence["worker_observations"]["parts"], strict=True
            ):
                area = sum(face["area_m2"] for face in actual["faces"])
                assert area == pytest.approx(limits["reference_area_m2"], rel=1e-8)
            reference = (analytic.directory / "export.stl").read_bytes()
            for h in (None, *policy["refinement_resolutions_m"]):
                pico_service = None
                try:
                    if h is None:
                        candidate, proof = analytic, evidence
                    else:
                        (tmp_path / ("pico-" + str(h))).mkdir()
                        pico_service = PicoBuildService(
                            PicoComponentAdapter(
                                "picogk", pico_worker, supervisor, enabled=True
                            ),
                            tmp_path / ("pico-" + str(h)),
                            PicoLimits.from_spec(qa(h)),
                        )
                        _, future = pico_service.submit(
                            pico_request(plan, h),
                            plan.snapshot,
                            field_graph(plan),
                            PicoReference(plan),
                        )
                        candidate = future.result(timeout=240)
                        assert candidate.record.state is BuildState.ACCEPTED, (
                            candidate.evidence_json
                        )
                        proof = json.loads(candidate.evidence_json)
                    raw = (candidate.directory / "export.stl").read_bytes()
                    payload = {
                        "snapshot_json": plan.snapshot.to_json(),
                        "graph_json": plan.graph.to_json(),
                        "policy": policy,
                        "reference_parts": evidence["worker_observations"]["parts"],
                        "candidate_parts": proof["worker_observations"]["parts"],
                        "reference_sha256": sha256(reference).hexdigest(),
                        "candidate_sha256": sha256(raw).hexdigest(),
                        "compare": h is not None,
                    }
                    result = runtime.run(reference, raw, payload, threading.Event())
                    result.update(
                        voxel_resolution_m=h, generation_process=proof["process"]
                    )
                    campaign.append(result)
                    assert result["pass"], json.dumps(result)
                finally:
                    if pico_service:
                        pico_service.close()
        finally:
            analytic_service.close()
            runtime.close()
    assert json.dumps(policy, sort_keys=True, allow_nan=False).encode() == policy_bytes
    record_property(
        "r08_family_campaign",
        json.dumps(
            {
                "kind": kind,
                "policy_sha256": sha256(policy_bytes).hexdigest(),
                "policy": policy,
                "campaign": campaign,
                "physical_validation": "NOT_PERFORMED",
            }
        ),
    )
