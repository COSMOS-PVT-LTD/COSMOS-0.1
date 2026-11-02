"""Actual two-kernel 3-resolution lifecycle; all reviewer accounts are fixtures."""

import json
import time
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from systems.geometry.qualification import QualificationRuntime
from tests.fixtures.component_geometry import qa_spec
from tests.fixtures.geometry_qualification import pipe_policy
from tests.integration_tests.geometry.test_pico_preview_native import workspace
from tests.integration_tests.gui.test_component_projects_http import (
    capture,
    compose,
    reviewer,
)
from tests.integration_tests.gui.test_engine_nozzle_projects_http import wait
from tests.integration_tests.gui.test_geometry_qualification_http import policy_command
from tests.integration_tests.gui.test_pressure_fed_projects_http import binary
from tests.integration_tests.gui.test_project_authority_http import request, running
from tests.unit_tests.systems_layer.test_pico_components import qa
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa:F401
)


def compose_r08(app):
    compose(app)
    pico = workspace(app.root / "r08-pico-candidates")
    app._pico_component_workspace = pico
    app.project_api.pico_components.coordinator.factory = lambda: pico
    cfg = {
        "python": str(
            Path(__file__).resolve().parents[3] / ".venv-release-p12/bin/python"
        )
    }
    runtime = QualificationRuntime(lambda: cfg)
    app.project_api.geometry_qualification.runtime = runtime
    return runtime


def test_actual_r08_predeclaration_both_kernels_refinement_review_export_and_restart(
    tmp_path, record_property
):
    store = tmp_path / "state"
    with running(store) as (app, base, client):
        runtime = compose_r08(app)
        project, _, root, model_command, saved = capture(
            app, base, client, "pipe.circular"
        )
        uri = root + "/geometry-qualifications"
        declared = pipe_policy()
        declared["boundaries"].append(
            {
                "part_id": "body",
                "semantic_id": "body:axial-start",
                "scope": "ANALYTIC_FACE",
                "purpose": "Exact independent imported face mapping fixture",
                "source": "Explicit annular cylinder start cap, not a solver boundary condition",
            }
        )
        p = request(client, base, uri + "/policies", policy_command(saved, declared))
        unsupported = deepcopy(declared)
        unsupported["boundaries"].append(
            {
                "part_id": "body",
                "semantic_id": "body:not-an-imported-face",
                "scope": "ANALYTIC_FACE",
                "purpose": "Deliberately unresolved fixture selection",
                "source": "Negative software test, never a valid boundary",
            }
        )
        unsupported["require_certified_self_intersection"] = True
        unsupported["parts"][0]["critical_features"][0]["surface_tolerance_m"] = 1e-12
        bad = request(
            client, base, uri + "/policies", policy_command(saved, unsupported)
        )
        command = {
            "model_commit_id": saved["authority"]["commit_id"],
            "expected_model": saved["authority"]["head"],
            "qa_specification": qa_spec(),
            "output_formats": ["step", "stl"],
            "operation_id": str(uuid4()),
        }
        begin = request(client, base, root + "/component-geometry-builds", command)
        analytic = wait(
            client,
            base,
            root
            + "/component-geometry-builds/"
            + begin["object_id"]
            + "/jobs/"
            + begin["job_id"],
        )
        assert analytic["state"] == "COMPLETED", analytic
        implicit = []
        for h in [0.0005, 0.00025, 0.000125]:
            begin = request(
                client,
                base,
                root + "/picogk-component-builds",
                {
                    **command,
                    "qa_specification": qa(h),
                    "output_formats": ["stl"],
                    "operation_id": str(uuid4()),
                },
            )
            result = wait(
                client,
                base,
                root
                + "/picogk-component-builds/"
                + begin["object_id"]
                + "/jobs/"
                + begin["job_id"],
            )
            assert result["state"] == "COMPLETED", result
            implicit.append(result["job_id"])
        cmd = {
            "policy_commit_id": p["authority"]["commit_id"],
            "analytic_job_id": analytic["job_id"],
            "implicit_job_ids": implicit,
            "operation_id": str(uuid4()),
        }
        started = request(client, base, uri + "/evaluate", cmd)
        path = uri + "/jobs/" + started["job_id"]
        assert (
            request(client, base, uri + "/evaluate", cmd)["job_id"] == started["job_id"]
        )
        result = wait(client, base, path)
        assert result["state"] == "COMPLETED", result
        report = result["report"]
        assert report["pass"], json.dumps(report)
        face = next(
            b for b in report["named_selections"] if b["scope"] == "ANALYTIC_FACE"
        )
        assert (
            face["entities"]
            and face["status"] == "EXACT_FOR_CAPTURED_ANALYTIC_REVISION"
        )
        assert len(report["campaign"]) == 4 and all(
            c["pass"] for c in report["campaign"]
        )
        assert [c["voxel_resolution_m"] for c in report["campaign"]] == [
            None,
            0.0005,
            0.00025,
            0.000125,
        ]
        assert (
            report["mesh_status"] == "NOT_GENERATED"
            and report["engineering_acceptance"] == "AWAITING_INDEPENDENT_REVIEW"
        )
        raw = binary(client, base, path + "/qualification.json")
        checksum = sha256(raw).hexdigest()
        # Lists are bounded lifecycle metadata, not repeated native artifact
        # validation or multi-megabyte copies of every qualification report.
        service = app.project_api.geometry_qualification.service
        original_report = service.report

        def no_report_in_history(*args, **kwargs):
            raise AssertionError(
                "History must not load/revalidate native report originals"
            )

        service.report = no_report_in_history
        try:
            rows = request(client, base, uri + "/jobs")["attempts"]
            assert rows and all(
                r["detail_required"]
                and "report" not in r
                and "events" not in r
                and "source_canonical_json" not in r
                for r in rows
            )
        finally:
            service.report = original_report
        # No retroactive policy, omitted resolution or client-generated approval.
        late = request(client, base, uri + "/policies", policy_command(saved))
        request(
            client,
            base,
            uri + "/evaluate",
            {
                **cmd,
                "policy_commit_id": late["authority"]["commit_id"],
                "operation_id": str(uuid4()),
            },
            expected=400,
        )
        request(
            client,
            base,
            uri + "/evaluate",
            {**cmd, "implicit_job_ids": implicit[:2], "operation_id": str(uuid4())},
            expected=400,
        )
        from dataclasses import asdict

        from systems.projects.authority import Head

        review = {
            "decision": "ACCEPT",
            "expected_job": result["head"],
            "expected_review": asdict(Head.absent()),
            "report_sha256": checksum,
            "qualification_source": "Synthetic second-account workflow fixture; NOT an actual independent engineering sign-off",
            "rationale": "Exercise preserved evidence-bound software contracts",
            "limitations": "No real engine, manufacturing or physical acceptance",
            "checks": dict.fromkeys(result["required_review_checks"], True),
            "operation_id": str(uuid4()),
        }
        request(client, base, path + "/review", review, expected=403)
        review_client = reviewer(app, base, client, project, root)
        request(
            review_client,
            base,
            path + "/review",
            {**review, "decision": [], "operation_id": str(uuid4())},
            expected=400,
        )
        request(
            review_client,
            base,
            path + "/review",
            {**review, "report_sha256": "0" * 64, "operation_id": str(uuid4())},
            expected=400,
        )
        accepted = request(
            review_client,
            base,
            path + "/review",
            {**review, "operation_id": str(uuid4())},
        )
        export = (
            uri + "/reviews/" + accepted["authority"]["object_id"] + "/handoff.json"
        )
        handoff = binary(client, base, export)
        assert json.loads(handoff)["mesh_status"] == "NOT_GENERATED"
        configuration = runtime.configuration
        runtime.configuration = lambda: {
            **configuration(),
            "changed-runtime-fixture": True,
        }
        assert not request(client, base, path)["upstream_current"]
        request(client, base, export, expected=400)
        runtime.configuration = configuration
        assert binary(client, base, export) == handoff
        # A completed computation containing an unmet requested check cannot pass.
        failed_start = request(
            client,
            base,
            uri + "/evaluate",
            {
                **cmd,
                "policy_commit_id": bad["authority"]["commit_id"],
                "operation_id": str(uuid4()),
            },
        )
        failed_path = uri + "/jobs/" + failed_start["job_id"]
        failed = wait(client, base, failed_path)
        assert failed["state"] == "COMPLETED" and not failed["report"]["pass"]
        assert failed["report"]["named_selections"][-1]["status"] == "UNRESOLVED"
        assert any(
            not f["pass"]
            for c in failed["report"]["campaign"]
            for p in c["parts"]
            for f in p["critical_features"]
        )
        badraw = binary(client, base, failed_path + "/qualification.json")
        request(
            review_client,
            base,
            failed_path + "/review",
            {
                **review,
                "expected_job": failed["head"],
                "report_sha256": sha256(badraw).hexdigest(),
                "operation_id": str(uuid4()),
            },
            expected=400,
        )
        cancelling = request(
            client, base, uri + "/evaluate", {**cmd, "operation_id": str(uuid4())}
        )
        cancel_path = uri + "/jobs/" + cancelling["job_id"]
        for _ in range(100):
            running_job = request(client, base, cancel_path)
            if running_job["state"] == "RUNNING":
                break
            time.sleep(0.02)
        assert running_job["state"] == "RUNNING"
        request(
            client,
            base,
            cancel_path + "/cancel",
            {"expected": running_job["head"], "operation_id": str(uuid4())},
        )
        cancelled = wait(client, base, cancel_path)
        assert cancelled["state"] == "CANCELLED" and not cancelled["blobs"]
        retried = request(
            client, base, cancel_path + "/retry", {"operation_id": str(uuid4())}
        )
        retry_result = wait(client, base, uri + "/jobs/" + retried["job_id"])
        assert retry_result["state"] == "COMPLETED" and retry_result["report"]["pass"]
        record_property(
            "r08_real_campaign",
            json.dumps(
                {
                    "project_id": project["project_id"],
                    "model_id": saved["authority"]["object_id"],
                    "state_root": str(store),
                    "qualification_job_id": started["job_id"],
                    "analytic_job_id": analytic["job_id"],
                    "implicit_job_ids": implicit,
                    "report_sha256": checksum,
                    "physical_validation": "NOT_PERFORMED",
                    "review": "SYNTHETIC_WORKFLOW_FIXTURE_ONLY",
                    "campaign": [
                        {
                            "h": c["voxel_resolution_m"],
                            "process": c["process"],
                            "pass": c["pass"],
                        }
                        for c in report["campaign"]
                    ],
                }
            ),
        )
    with running(store) as (app, base, client):
        compose_r08(app)
        assert binary(client, base, path + "/qualification.json") == raw
        assert binary(client, base, export) == handoff
        review_client = reviewer_relogin(base)
        rejected = request(
            review_client,
            base,
            path + "/review",
            {
                **review,
                "decision": "REJECT",
                "expected_review": accepted["authority"]["head"],
                "operation_id": str(uuid4()),
            },
        )
        assert rejected["record"]["engineering_acceptance"] == "REJECTED"
        request(client, base, export, expected=400)
        edited = request(
            client,
            base,
            root + "/component-geometry/" + saved["authority"]["object_id"],
            {
                **model_command,
                "title": "Synthetic revised pipe: new policy/review required",
                "expected": saved["authority"]["head"],
                "operation_id": str(uuid4()),
            },
        )
        assert not request(client, base, path)["upstream_current"]
        remap = request(
            client,
            base,
            uri + "/remap-proposal",
            {
                "review_commit_id": accepted["authority"]["commit_id"],
                "new_model_commit_id": edited["authority"]["commit_id"],
            },
        )
        assert (
            not remap["persisted"]
            and not remap["handoff_eligible"]
            and remap["mappings"][0]["status"] == "PROPOSED_UNREVIEWED"
        )


def reviewer_relogin(base):
    from tests.integration_tests.gui.test_project_authority_http import client_for

    return client_for(base, "component-reviewer", "Synthetic-Review-Only!", "USER")
