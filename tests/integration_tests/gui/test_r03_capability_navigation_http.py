"""Catalog/route consistency on an isolated local preview, not a release gate."""
from __future__ import annotations

import json
import threading

import pytest

from gui.server import CosmosApplication, CosmosApplicationHandler
from infrastructure.release.security import PreviewHTTPServer
from tests.integration_tests.gui.test_r01_authorization_http import call


@pytest.mark.parametrize("shell,features", [(True, True), (True, False), (False, True)])
def test_enabled_capabilities_and_routes_are_consistent(tmp_path, monkeypatch, shell, features):
    monkeypatch.setenv("COSMOS_RELEASE_PROFILE", "local-preview")
    app = CosmosApplication(tmp_path, new_shell=shell, simulation_enabled=features,
        comparison_enabled=features, knowledge_reports_enabled=features)

    class Handler(CosmosApplicationHandler):
        application = app
        def log_message(self, *_args):
            pass

    server = PreviewHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        auth = json.loads((app.root / "first-login.json").read_text())
        status, headers, _ = call(server, "/api/auth/login", auth | {"login_profile": "ADMIN"})
        assert status == 200
        token = headers["Set-Cookie"].split(";", 1)[0]
        status, _, body = call(server, "/api/workbenches", token=token)
        assert status == 200
        catalog = {item["workbench_id"]: item for page in json.loads(body)["pages"] for item in page["items"]}
        active = shell and features
        for identifier, route in (("simulation", "/app/workbench/simulation"),
            ("comparison", "/app/workbench/comparison"), ("reports", "/app/workbench/reports")):
            item = catalog.get(identifier)
            assert bool(item and item["status"] == "active") is active
            if active:
                assert item["route"] == route
                assert call(server, route, token=token)[0] == 200
        assert catalog["visualization"]["status"] == "active"
        assert catalog["visualization"]["validation_state"] == "SOURCE_VIEW_ONLY"
        assert catalog["code-comparison"]["status"] == "planned"
        assert catalog["rocket-engine"]["status"] == "active"
        status, headers, _ = call(server, "/app/projects?view=history", token=token)
        if not shell:
            assert status == 302
            assert headers["Location"] == "/app/workbenches"
        else:
            assert status == 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
