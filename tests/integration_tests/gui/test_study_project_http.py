"""Managed study transport denial/capabilities; no fake native success."""
from __future__ import annotations

import sqlite3
import urllib.request
from dataclasses import asdict
from uuid import uuid4

import pytest

from infrastructure.persistence.schema import APPLICATION_ID, SCHEMA_V4
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import Head, Principal
from tests.integration_tests.gui.test_project_authority_http import (
    new_project,
    request,
    running,
)

VALUES = {"conductivity_w_m_k": 10., "generation_w_m3": 1e6, "surface_k": 300., "cells": 16,
          "relative_residual": 1e-8, "max_iterations": 10_000}


def body(**extra):
    return {"settings": VALUES, "expected": asdict(Head.absent()), "geometry_job_id": str(uuid4()), "operation_id": str(uuid4()), **extra}


@pytest.mark.parametrize("extra", [{"owner_user_id": "forged"}, {"solver_command": "forbidden"}, {"path": "/tmp"}, {"dataset": {"temperature_k": [999]}}])
def test_posted_identity_path_solver_or_results_refused(tmp_path, extra):
    with running(tmp_path / "app") as (_app, base, client):
        project = new_project(base, client)
        request(client, base, f"/api/projects/{project['project_id']}/studies", body(**extra), expected=400)


def test_study_capabilities_auth_paging_and_no_legacy_backend_activation(tmp_path):
    with running(tmp_path / "app") as (app, base, client):
        project = new_project(base, client)
        path = f"/api/projects/{project['project_id']}/studies"
        data = request(client, base, path)
        assert not data["objects"] and data["default_settings"] == VALUES
        assert request(client, base, "/api/ui/shell")["durableProjects"]["managedStudies"] is True
        request(urllib.request.build_opener(), base, path, expected=401)
        request(client, base, path+"?limit=1000", expected=400)
        request(client, base, path, body(), expected=404)
        assert app._simulation_workspace is None and app._ngg_workspace is None


@pytest.mark.parametrize("settings", [{"cells": 16}, {**VALUES, "cells": 128}, {**VALUES, "conductivity_w_m_k": -1}, {**VALUES, "automatic_cea": True}])
def test_settings_are_complete_explicit_and_existing_bounded_contract(tmp_path, settings):
    with running(tmp_path / "app") as (_app, base, client):
        project = new_project(base, client)
        request(client, base, f"/api/projects/{project['project_id']}/studies", body(settings=settings), expected=400)


def test_old_schema4_never_upgrades_and_study_routes_fail_closed(tmp_path):
    root = tmp_path / "old-app"
    store = root / "engineering_state" / "v1"
    store.mkdir(mode=0o700, parents=True)
    store.parent.chmod(0o700)
    database = store / "metadata.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.executescript(SCHEMA_V4 + f"PRAGMA user_version=4; PRAGMA application_id={APPLICATION_ID};")
    database.chmod(0o600)
    repo = SQLiteProjectRepository(store)
    project = repo.create_project(Principal("USR-old-root", "ENGINEER"), title="Existing synthetic schema4", operation_id="create")
    before = database.read_bytes()
    with running(root) as (app, base, client):
        # No actor guessed from a legacy source namespace: bootstrap admin is not this owner.
        request(client, base, f"/api/projects/{project.project_id}/studies", expected=403)
        assert app.project_api.studies is None
        assert request(client, base, "/api/ui/shell")["durableProjects"]["managedStudies"] is False
    assert database.read_bytes() == before
