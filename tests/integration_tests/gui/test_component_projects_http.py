"""Exact authorized component editor → real native candidate → review → setup."""

import json
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pytest

from api.authentication import UserRole
from api.project_authority import principal
from systems.geometry.component_workspace import ComponentWorkspace
from systems.projects.authority import Head
from tests.fixtures.component_geometry import model, qa_spec
from tests.fixtures.coupled_cycle import design
from tests.integration_tests.geometry.test_component_native import commands
from tests.integration_tests.gui.test_engine_nozzle_projects_http import wait
from tests.integration_tests.gui.test_pressure_fed_projects_http import binary
from tests.integration_tests.gui.test_project_authority_http import (
    client_for,
    new_project,
    request,
    running,
)
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


def capture(app, base, client, kind="cooling.axial_sector"):
    project = new_project(base, client)
    actor = principal(app.auth.list_users()[0])
    source = app.project_api.service.create(actor, project["project_id"], design=design(cooling=True), operation_id="baseline", command_hash="1" * 64)
    root = "/api/projects/" + project["project_id"]
    command = {"title": "Synthetic component qualification only", "baseline_commit_id": source.commit_id, "expected_baseline": asdict(source.head), "specification": model(kind), "expected": asdict(Head.absent()), "operation_id": str(uuid4())}
    saved = request(client, base, root + "/component-geometry", command)
    return project, source, root, command, saved


def compose(app):
    worker = commands()
    reader = {"argv": [worker.argv[0], str(Path(worker.argv[1]).with_name("component_step_reader.py"))], "environment": dict(worker.environment)}
    cfg = {"sha256": {"explicit-test-runtime": "1" * 64}, "manifest_sha256": "2" * 64, "engine_components": {"worker": {"argv": list(worker.argv), "environment": dict(worker.environment)}, "reader": reader}}
    workspace = ComponentWorkspace(app.root / "component-test-candidates", lambda: cfg)
    app._component_workspace = workspace
    app.project_api.components.builds.coordinator.factory = lambda: workspace


def reviewer(app, base, client, project, root):
    user = app.auth.register_user(login_id="component-reviewer", password="Synthetic-Review-Only!", display_name="Synthetic workflow reviewer NOT real acceptance", designation="Software test", employee_id="CMP-TEST", team="QA", role=UserRole.ENGINEER)
    request(client, base, root + "/members", {"user_id": user.user_id, "capability": "EDITOR", "expected": request(client, base, root)["project"]["head"], "operation_id": str(uuid4())})
    return client_for(base, "component-reviewer", "Synthetic-Review-Only!", "USER")


def review_command(context):
    return {"decision": "ACCEPT", "intended_use": "GEOMETRY_ANALYSIS_PREPARATION", "qualification_source": "Synthetic workflow test only; NOT a real engineer sign-off", "rationale": "Exercise exact software contracts", "limitations": "No hardware/manufacturing/physical or real-human acceptance", "checks": dict.fromkeys(context["required_checks"], True), "artifact_sha256": context["artifact_sha256"], "expected_job": context["job_head"], "operation_id": str(uuid4()), "material_regions": [{"part_id": p["part_id"], "kind": p["role"], "material_name": "Synthetic labeled region", "source": "Test-only label, no solver properties"} for p in context["parts"]], "mesh_constraints": {"maximum_edge_m": .00025, "minimum_feature_m": .001, "cells_across_feature": 4, "curvature_tolerance_m": .00001, "maximum_cells": 100000, "source": "Synthetic software mesh-intent test; mesh NOT generated"}}


def test_component_editor_preview_cas_history_restore_units_and_project_scope(tmp_path):
    with running(tmp_path / "state") as (app, base, client):
        project, baseline, root, command, saved = capture(app, base, client)
        uri = root + "/component-geometry/" + saved["authority"]["object_id"]
        assert saved["usable_current_model"] and len(saved["parts"]) == 5
        assert request(client, base, root + "/component-geometry", command)["authority"] == saved["authority"]
        preview = request(client, base, root + "/component-geometry/preview", {"object_id": saved["authority"]["object_id"], "specification": command["specification"]})
        assert not preview["persisted"]
        changed = deepcopy(command); changed["expected"] = saved["authority"]["head"]; changed["operation_id"] = str(uuid4())
        changed["specification"]["features"][1]["parameters"]["phase"]["value"] = .2
        edited = request(client, base, uri, changed)
        assert edited["authority"]["head"]["version"] == 2
        request(client, base, uri, {**command, "operation_id": str(uuid4())}, expected=409)
        assert not request(client, base, uri + "?commit=" + saved["authority"]["commit_id"])["upstream_current"]
        restored = request(client, base, uri + "/restore", {"origin_commit_id": saved["authority"]["commit_id"], "expected": edited["authority"]["head"], "expected_baseline": asdict(baseline.head), "operation_id": str(uuid4())})
        assert restored["model"]["specification"] == command["specification"]
        assert restored["authority"]["head"]["version"] == 3
        assert len(request(client, base, uri + "/history")["commits"]) == 3
        invalid = deepcopy(command["specification"]); invalid["features"][1]["parameters"]["depth"]["unit"] = "mm"
        request(client, base, root + "/component-geometry/preview", {"object_id": None, "specification": invalid}, expected=400)
        request(client, base, root + "/component-geometry/capabilities?commit=ignored", expected=400)
        other = new_project(base, client)
        request(client, base, "/api/projects/" + other["project_id"] + "/component-geometry/" + saved["authority"]["object_id"], expected=404)
        assert app.project_api.repository.resolve_snapshot(principal(app.auth.list_users()[0]), project["project_id"], baseline.commit_id).payload == baseline.payload
        original = binary(client, base, uri + "/record.json")
    with running(tmp_path / "state", enabled=False) as (_, base, client):
        assert binary(client, base, uri + "/record.json") == original


def test_component_seed_requires_current_solved_source_and_explicit_missing_dimensions(tmp_path):
    with running(tmp_path / "state") as (app, base, client):
        _, baseline, root, _, _ = capture(app, base, client, "profile.wall")
        q = lambda v: {"value": v, "unit": "m"}
        settings = {"wall_thickness": q(.004), "convergent_length": q(.04), "throat_land_length": q(.003), "source_tolerance": q(1e-6), "export_tolerance": q(2e-5), "source": "Explicit test-only CAD dimensions"}
        value = request(client, base, root + "/component-geometry/seed-from-design", {"baseline_commit_id": baseline.commit_id, "settings": settings})
        assert len(value["specification"]["features"]) == 1 and value["warnings"]
        assert value["specification"]["features"][0]["parameters"]["point_count"]["value"] > 80
        request(client, base, root + "/component-geometry/seed-from-design", {"baseline_commit_id": baseline.commit_id, "settings": {"source": "No guessed dimensions"}}, expected=400)


def test_hydraulic_biprop_seed_and_managed_save_cannot_resize_source_ports(tmp_path):
    from core.serialization import canonical_json_dumps
    from systems.configuration.subsystems import configure_subsystems
    from systems.stages.subsystems import run_injector_stage
    with running(tmp_path/"state") as (app,base,client):
        project=new_project(base,client); actor=principal(app.auth.list_users()[0])
        baseline_design=design(cooling=True)
        cfg={**baseline_design.subsystem_inputs["injector"],"fuel_hole_count":8,"oxidizer_hole_count":8}
        configure_subsystems(baseline_design,{"injector":cfg})
        assert run_injector_stage(baseline_design).status.value=="CURRENT"
        source=app.project_api.service.create(actor,project["project_id"],design=baseline_design,operation_id="hydraulic-source",command_hash="1"*64)
        root="/api/projects/"+project["project_id"]
        q=lambda v,u="m":{"value":v,"unit":u}
        settings={"radius":q(.06),"thickness":q(.004),"ring_radius":q(.035),"separation":q(.012),"angle":q(.2,"rad"),"phase":q(0,"rad"),
                  "source_tolerance":q(1e-6),"export_tolerance":q(2e-5),"source":"Synthetic API source-binding test; not an engine design"}
        seeded=request(client,base,root+"/component-geometry/seed-injector-from-design",{"baseline_commit_id":source.commit_id,"settings":settings})
        inputs=seeded["specification"]["features"][0]["parameters"]
        retained=json.loads(source.payload)["workflow"]["results"]["injector"]["outputs"]
        for name in ("fuel","oxidizer"):
            wanted=q(retained[name]["diameter_m"]/2)
            assert canonical_json_dumps(inputs[name+"_hole_radius"])==canonical_json_dumps(wanted)
        assert inputs["count"]==q(8,"1") and seeded["injector_result_id"]
        body={"title":"Source-bound software fixture","baseline_commit_id":source.commit_id,"expected_baseline":asdict(source.head),
              "specification":seeded["specification"],"expected":asdict(Head.absent()),"operation_id":str(uuid4())}
        saved=request(client,base,root+"/component-geometry",body)
        assert saved["usable_current_model"]
        resized=deepcopy(body); resized["operation_id"]=str(uuid4()); resized["specification"]["features"][0]["parameters"]["fuel_hole_radius"]["value"]*=1.01
        error=request(client,base,root+"/component-geometry",resized,expected=400)
        assert "hydraulic source" in str(error)
        request(client,base,root+"/component-geometry/seed-injector-from-design",{"baseline_commit_id":source.commit_id,"settings":{**settings,"fuel_hole_radius":q(.001)}},expected=400)
        mutated=app.project_api.service.edit(actor,project["project_id"],source.object_id,expected=source.head,
            operation_id="change-source",command_hash="2"*64,mutate=lambda d:configure_subsystems(d,{"injector":{**cfg,"fuel_cd":.6}}))
        assert not request(client,base,root+"/component-geometry/"+saved["authority"]["object_id"])["upstream_current"]
        request(client,base,root+"/component-geometry/seed-injector-from-design",{"baseline_commit_id":source.commit_id,"settings":settings},expected=400)
        request(client,base,root+"/component-geometry/seed-injector-from-design",{"baseline_commit_id":mutated.commit_id,"settings":settings},expected=400)


def test_real_native_component_review_handoff_staleness_originals_and_restart(tmp_path):
    commands()
    with running(tmp_path / "state") as (app, base, client):
        compose(app)
        project, _, root, command, saved = capture(app, base, client)
        prefix = root + "/component-geometry-builds"
        body = {"model_commit_id": saved["authority"]["commit_id"], "expected_model": saved["authority"]["head"], "qa_specification": qa_spec(), "output_formats": ["step", "stl"], "operation_id": str(uuid4())}
        initial = request(client, base, prefix, body)
        assert request(client, base, prefix, body)["job_id"] == initial["job_id"]
        path = prefix + "/" + initial["object_id"] + "/jobs/" + initial["job_id"]
        result = wait(client, base, path)
        assert result["state"] == "COMPLETED", result["source_canonical_json"]
        context = request(client, base, path + "/review-context")
        assert context["reviewer_is_builder"] and len(context["parts"]) == 5 and context["interfaces"]
        section = request(client, base, path + "/sections?part_id=channels&x_m=0.02")
        assert section["section"]["area_m2"] > 0 and section["geometry_revision_id"]
        request(client, base, path + "/sections?part_id=channels&x_m=NaN", expected=400)
        review = review_command(context)
        request(client, base, root + "/component-geometry-reviews", {"job_id": initial["job_id"], "review": review}, expected=403)
        other = reviewer(app, base, client, project, root)
        bad = deepcopy(review); bad["checks"][context["required_checks"][0]] = False; bad["operation_id"] = str(uuid4())
        request(other, base, root + "/component-geometry-reviews", {"job_id": initial["job_id"], "review": bad}, expected=400)
        rejected = deepcopy(review); rejected["decision"] = "REJECT"; rejected["operation_id"] = str(uuid4())
        denied = request(other, base, root + "/component-geometry-reviews", {"job_id": initial["job_id"], "review": rejected})
        request(client, base, root + "/component-studies", {"review_commit_id": denied["authority"]["commit_id"], "operation_id": str(uuid4())}, expected=400)
        accepted = request(other, base, root + "/component-geometry-reviews", {"job_id": initial["job_id"], "review": review})
        assert json.loads(accepted["record"]["published_record_json"])["events"][-1]["state"] == "published"
        setup_body = {"review_commit_id": accepted["authority"]["commit_id"], "operation_id": str(uuid4())}
        setup = request(client, base, root + "/component-studies", setup_body)
        assert request(client, base, root + "/component-studies", setup_body)["authority"] == setup["authority"]
        contracts = json.loads(setup["record"]["setup_json"])
        assert contracts["solver_supported"] is False and contracts["mesh_status"] == "NOT_GENERATED"
        assert len(contracts["handoff"]["material_regions"]) == 5 and contracts["handoff"]["interfaces"]
        setup_uri = root + "/component-studies/" + setup["authority"]["object_id"]
        original = binary(client, base, path + "/blobs/export.step")
        assert sha256(original).hexdigest() == contracts["handoff"]["geometry_integrity_sha256"]
        assert binary(client, base, setup_uri + "/blobs/export.step") == original
        command.update(expected=saved["authority"]["head"], operation_id=str(uuid4()))
        command["specification"]["features"][1]["parameters"]["phase"]["value"] = .2
        edited = request(client, base, root + "/component-geometry/" + saved["authority"]["object_id"], command)
        assert not request(client, base, setup_uri)["upstream_current"]
        request(client, base, setup_uri + "/blobs/export.step", expected=400)
        assert binary(client, base, path + "/blobs/export.step") == original
        body.update(model_commit_id=edited["authority"]["commit_id"], expected_model=edited["authority"]["head"], operation_id=str(uuid4()))
        new = request(client, base, prefix, body)
        newer = wait(client, base, prefix + "/" + new["object_id"] + "/jobs/" + new["job_id"])
        assert newer["state"] == "COMPLETED", newer["source_canonical_json"]
        proposal = request(client, base, root + "/component-geometry-reviews/remap-proposal", {"review_commit_id": accepted["authority"]["commit_id"], "new_job_id": new["job_id"]})
        assert proposal["handoff_eligible"] is False and proposal["persisted"] is False
        assert all(s["mapping_status"] in {"remapped", "unresolved"} for s in proposal["named_selections"])
    with running(tmp_path / "state", enabled=False) as (_, base, client):
        assert binary(client, base, path + "/blobs/export.step") == original
        assert not request(client, base, setup_uri)["upstream_current"]


def test_actual_component_failed_qa_and_exact_cancellation_do_not_publish_partial_geometry(tmp_path):
    commands()
    with running(tmp_path / "state") as (app, base, client):
        compose(app)
        project, _, root, _, saved = capture(app, base, client, "profile.wall")
        body={"model_commit_id":saved["authority"]["commit_id"],"expected_model":saved["authority"]["head"],"qa_specification":qa_spec(),"output_formats":["step","stl"],"operation_id":str(uuid4())}
        body["qa_specification"]["relative_volume"]["value"]=1e-14
        prefix=root+"/component-geometry-builds"; initial=request(client,base,prefix,body)
        path=prefix+"/"+initial["object_id"]+"/jobs/"+initial["job_id"]
        result=wait(client,base,path)
        assert result["state"]=="FAILED" and not result["blobs"] and not result["current_generated_candidate"]
        request(client,base,path+"/preview",expected=400); request(client,base,path+"/review-context",expected=400)
        body["qa_specification"]=qa_spec();body["operation_id"]=str(uuid4())
        coordinator=app.project_api.components.builds.coordinator; original=coordinator.reference; entered=[]
        def cancel_reference(revision):
            live=next(iter(coordinator.live));actor=principal(app.auth.list_users()[0]);job=coordinator.jobs.get(actor,project["project_id"],live)
            coordinator.cancel(actor,project["project_id"],live,expected=job.head,operation_id="component-cancel",request_hash="6"*64)
            entered.append(live);return original(revision)
        coordinator.reference=cancel_reference
        newer=request(client,base,prefix,body);cancelled=wait(client,base,prefix+"/"+newer["object_id"]+"/jobs/"+newer["job_id"])
        assert entered and cancelled["state"]=="CANCELLED" and not cancelled["blobs"] and not cancelled["selected_attempt"]


@pytest.mark.parametrize("extra", [{"engineering_acceptance": True}, {"solver": "engine-cfd"}])
def test_component_input_never_accepts_posted_acceptance_or_solver_authority(tmp_path, extra):
    with running(tmp_path / "state") as (app, base, client):
        _, _, root, command, _ = capture(app, base, client, "profile.wall")
        request(client, base, root + "/component-geometry", {**command, **extra, "operation_id": str(uuid4())}, expected=400)
