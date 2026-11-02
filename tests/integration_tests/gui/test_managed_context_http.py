"""Real authenticated context/history/clone/package HTTP in isolated roots."""
from __future__ import annotations

import base64
from dataclasses import asdict
from uuid import uuid4

from systems.projects.authority import Head
from tests.integration_tests.gui.test_geometry_project_http import create, url
from tests.integration_tests.gui.test_project_authority_http import (
    new_design,
    new_project,
    request,
    running,
)


def test_owned_context_records_history_activate_branch_requirements_and_clone(tmp_path):
    with running(tmp_path / "source") as (app, base, client):
        project = new_project(base, client)
        prefix = "/api/projects/" + project["project_id"]
        design = new_design(base, client, project)
        geometry = create(base, client, project)
        first = geometry["authority"]
        second = request(client, base, url(project, geometry), {"settings": {"operation": "union", "backend": "occt", "voxel_m": .0005}, "expected": first["head"], "operation_id": str(uuid4())})
        assert "geometry-fixture" in request(client, base, prefix + "/domains")["domains"]
        source = request(client, base, prefix + "/records/" + first["commit_id"])
        assert source["source_canonical_json"] == geometry["source_canonical_json"] and not source["authority"]["is_current"]
        path = prefix + "/records/" + first["commit_id"]
        activated = request(client, base, path + "/activate", {"expected": second["authority"]["head"], "operation_id": str(uuid4())})
        assert activated["source_canonical_json"] == source["source_canonical_json"] and activated["authority"]["input_revision"] == 2
        branch = request(client, base, path + "/branch", {"expected": activated["authority"]["head"], "operation_id": str(uuid4())})
        assert branch["authority"]["object_id"] != first["object_id"] and branch["origin"] == path
        assert not request(client, base, prefix + "/jobs")["attempts"]
        history = request(client, base, prefix + "/objects/geometry-fixture/" + first["object_id"] + "/history")
        assert len(history["commits"]) == 3
        requirements = request(client, base, prefix + "/requirements", {"requirements": ["Synthetic software requirement only"],
            "components": [activated["authority"]["commit_id"]], "expected": asdict(Head.absent()), "operation_id": str(uuid4())})
        assert requirements["upstream"][0]["commit_id"] == activated["authority"]["commit_id"]
        clone_body = {"title": "Inputs clone — synthetic", "expected": project["head"], "operation_id": str(uuid4())}
        clone = request(client, base, prefix + "/clone", clone_body)["project"]
        assert clone["project_id"] != project["project_id"]
        assert request(client, base, prefix + "/clone", clone_body)["project"] == clone
        cloned = request(client, base, "/api/projects/" + clone["project_id"] + "/context?domain=propulsion")
        assert len(cloned["objects"]) == 1 and cloned["objects"][0]["object_id"] != design["design"]["design_id"]
        assert any(e["action"] == "project.cloned" for e in request(client, base, "/api/projects/" + clone["project_id"] + "/timeline")["events"])
        origins = request(client, base, "/api/projects/" + clone["project_id"] + "/transfers")["transfers"]
        assert len(origins) == 1 and origins[0]["kind"] == "clone-origin"
        with client.open(base + "/api/projects/" + clone["project_id"] + "/transfers/" + origins[0]["receipt_id"]) as response:
            assert response.read().startswith(b"PK")
        other = new_project(base, client, "Other owning project")
        request(client, base, "/api/projects/" + other["project_id"] + "/records/" + first["commit_id"], expected=404)
        root = app.root
    with running(root, enabled=False) as (_app, base, client):
        assert request(client, base, prefix + "/records/" + first["commit_id"])["source_canonical_json"] == geometry["source_canonical_json"]
        request(client, base, path + "/activate", {"expected": activated["authority"]["head"], "operation_id": str(uuid4())}, expected=403)


def test_project_package_http_preview_explicit_mapping_and_flag_off_protection(tmp_path):
    with running(tmp_path / "source") as (_app, base, client):
        project = new_project(base, client)
        design = new_design(base, client, project)
        prefix = "/api/projects/" + project["project_id"]
        with client.open(base + prefix + "/package?version=1&hash=" + project["head"]["content_hash"]) as response:
            raw = response.read()
    with running(tmp_path / "target") as (app, base, client):
        actor = app.auth.get_user("cosmos-admin") if hasattr(app.auth, "get_user") else app.auth.list_users()[0]
        body = {"package_base64": base64.b64encode(raw).decode()}
        preview = request(client, base, "/api/projects/import-preview", body)["preview"]
        users = {key: actor.user_id for key in preview["required_explicit_user_mapping"]}
        imported = request(client, base, "/api/projects/import", {**body, "confirmed_manifest_sha256": preview["manifest_sha256"], "user_mapping": users, "confirmed_memberships": True})
        assert imported["import"]["project_id"] == project["project_id"]
        source = request(client, base, prefix + "/designs/" + design["design"]["design_id"])
        assert source["source_canonical_json"] == design["source_canonical_json"]
        request(client, base, "/api/projects/import-preview", {**body, "role": "ADMIN"}, expected=400)
