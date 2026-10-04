"""HTTP end-to-end: login → one design → phase 3 → Pc change → stale → save/reload."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http import cookiejar
from http.server import HTTPServer
from pathlib import Path

import pytest

from gui.server import CosmosApplicationHandler


def _start_server(tmp_path: Path) -> tuple[str, HTTPServer]:
    from gui.server import CosmosApplication

    class Handler(CosmosApplicationHandler):
        application = CosmosApplication(tmp_path)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return f"http://{host}:{port}", server


def _client() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookiejar.CookieJar())
    )


def _json(
    opener: urllib.request.OpenerDirector,
    url: str,
    payload: dict | None = None,
    method: str = "GET",
):
    headers = {"Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    return json.loads(opener.open(request, timeout=30).read())


def test_propulsion_design_lifecycle_http(tmp_path: Path) -> None:
    base, server = _start_server(tmp_path)
    opener = _client()
    try:
        login = _json(
            opener,
            f"{base}/api/auth/login",
            {
                "login_id": "cosmos-admin",
                "password": "COSMOS-Dev-2026!",
                "login_profile": "ADMIN",
            },
            method="POST",
        )
        assert login["user"]["role"] == "ADMIN"

        rocket = (
            opener.open(f"{base}/app/workbench/rocket-engine", timeout=5)
            .read()
            .decode("utf-8")
        )
        assert "cosmos-api.js" in rocket
        assert "design-context-bar" in rocket
        assert "design-recalculate" in rocket
        assert "propulsion-workbench" in rocket
        assert 'id="maharshi-module"' not in rocket
        propulsion_js = (
            opener.open(f"{base}/assets/propulsion-suite.js", timeout=5)
            .read()
            .decode("utf-8")
        )
        assert "runWorkflowFromDesign" in propulsion_js
        assert "displayEngineQty" in propulsion_js

        catalog = _json(opener, f"{base}/api/propulsion/workflow-catalog")
        assert catalog["nodes"][0]["stage_id"] == "design_project"
        assert catalog["nodes"][-1]["stage_id"] == "design_review"
        assert catalog["nodes"][0]["stage_index"] == "00"
        chamber_node = next(
            node for node in catalog["nodes"] if node["stage_id"] == "chamber"
        )
        assert all(isinstance(stage, str) for stage in chamber_node["dependencies"])
        assert any(
            edge["stage_id"] == "injector" and edge["requirement"] == "DEFERRED"
            for edge in chamber_node["dependency_edges"]
        )

        api_js = (
            opener.open(f"{base}/assets/cosmos-api.js", timeout=5)
            .read()
            .decode("utf-8")
        )
        assert "listDesigns" in api_js

        help_page = opener.open(f"{base}/app/help", timeout=5).read().decode("utf-8")
        assert "cosmos-admin" in help_page

        created = _json(
            opener,
            f"{base}/api/propulsion/designs",
            {"name": "E2E Engine"},
            method="POST",
        )
        design_id = created["design"]["design_id"]

        for missing_or_unknown in ("", "unknown-oxidizer"):
            with pytest.raises(urllib.error.HTTPError) as captured:
                _json(
                    opener,
                    f"{base}/api/propulsion/designs/{design_id}/propellants",
                    {
                        "oxidizer_id": missing_or_unknown,
                        "fuel_id": "RP1",
                        "mixture_ratio": 2.3,
                    },
                    method="POST",
                )
            assert captured.value.code == 400
            failure = json.loads(captured.value.read())
            assert failure["error"]["code"] == "PropellantNotFoundError"
            assert "Alias not found" in failure["error"]["message"]

        listed = _json(opener, f"{base}/api/propulsion/designs")
        assert any(row["design_id"] == design_id for row in listed["designs"])

        _json(
            opener,
            f"{base}/api/propulsion/designs/{design_id}/requirements",
            {
                "updates": {
                    "target_chamber_pressure": {"magnitude": 50, "unit_symbol": "bar"},
                    "target_thrust": {"magnitude": 10, "unit_symbol": "kN"},
                    "mixture_ratio": 2.3,
                    "expansion_ratio": 8.0,
                    "ambient_pressure": {"magnitude": 101325, "unit_symbol": "Pa"},
                }
            },
            method="POST",
        )
        _json(
            opener,
            f"{base}/api/propulsion/designs/{design_id}/propellants",
            {"oxidizer_id": "LOX", "fuel_id": "RP1", "mixture_ratio": 2.3},
            method="POST",
        )
        phase3 = _json(
            opener,
            f"{base}/api/propulsion/designs/{design_id}/run/phase3",
            {
                "chamber_temperature_k": 3000.0,
                "gamma": 1.2,
                "molecular_weight_kg_per_mol": 0.022,
                "throat_area_m2": 0.01,
                "expansion_ratio": 8.0,
            },
            method="POST",
        )
        assert phase3["ok"] is True
        assert phase3["phase_status"] == "PARTIAL"
        assert phase3["stages"]["performance"]["status"] == "CURRENT"
        assert phase3["execution_ok"] is True
        assert phase3["workflow_complete"] is False
        assert phase3["engineering_readiness"] == "PRELIMINARY"
        assert phase3["validation_level"] == "NOT_CLAIMED"

        qualified_phase4 = _json(
            opener,
            f"{base}/api/propulsion/designs/{design_id}/run/phase4",
            {
                "characteristic_length_m": 1,
                "contraction_ratio": 2.5,
                "wall_thickness_m": 0.006,
                "material_id": "stainless_304",
                "external_pressure_pa": 0,
                "external_pressure_source": "Explicit E2E vacuum boundary",
                "material_temperature_k": 300,
                "viscosity_pa_s": 8e-5,
                "conductivity_w_m_k": 0.3,
                "cp_j_kg_k": 2500,
                "wall_temperature_k": 800,
            },
            method="POST",
        )
        assert qualified_phase4["execution_ok"] is True
        assert qualified_phase4["workflow_complete"] is False
        assert (
            qualified_phase4["stages"]["structure"]["inputs"][
                "external_pressure_source"
            ]
            == "Explicit E2E vacuum boundary"
        )
        reviewed = _json(
            opener,
            f"{base}/api/propulsion/designs/{design_id}/run/phase6",
            {},
            method="POST",
        )
        assert reviewed["execution_ok"] is True
        assert (
            reviewed["stages"]["design_review"]["outputs"]["review_verdict"]
            == "INCOMPLETE"
        )
        exported = _json(opener, f"{base}/api/propulsion/designs/{design_id}/export")
        assert exported["package"]["readiness"]["workflow_complete"] is False

        after_phase3 = _json(opener, f"{base}/api/propulsion/designs/{design_id}")
        assert after_phase3["design"]["nozzle_design"]["geometry_status"] == "CURRENT"

        _json(
            opener,
            f"{base}/api/propulsion/designs/{design_id}/requirements",
            {
                "updates": {
                    "target_chamber_pressure": {"magnitude": 70, "unit_symbol": "bar"}
                }
            },
            method="POST",
        )
        after_pc = _json(opener, f"{base}/api/propulsion/designs/{design_id}")
        assert after_pc["design"]["nozzle_design"]["geometry_status"] == "STALE"
        workflow = _json(opener, f"{base}/api/propulsion/designs/{design_id}/workflow")
        performance = next(
            node
            for node in workflow["workflow"]["nodes"]
            if node["stage_id"] == "performance"
        )
        assert performance["status"] == "STALE"
        assert performance["result_is_current"] is False

        saved = _json(
            opener,
            f"{base}/api/propulsion/designs/{design_id}/save",
            {},
            method="POST",
        )
        assert saved["ok"] is True
        reloaded = _json(opener, f"{base}/api/propulsion/designs/{design_id}")
        assert reloaded["design"]["design_id"] == design_id
        assert reloaded["design"]["name"] == "E2E Engine"

        phase4 = _json(
            opener,
            f"{base}/api/propulsion/designs/{design_id}/run/phase4",
            {
                "characteristic_length_m": 1.0,
                "contraction_ratio": 2.5,
                "wall_thickness_m": 0.006,
                "material_id": "stainless_304",
            },
            method="POST",
        )
        # Phase 3 is stale after Pc change; phase 4 chamber may fail without CURRENT performance.
        assert phase4["stages"]["injector"]["status"] == "NOT_IMPLEMENTED"
        assert phase4["stages"]["cooling"]["status"] == "NOT_IMPLEMENTED"
        assert phase4["ok"] is False or phase4["phase_status"] in {"PARTIAL", "FAILED"}
    finally:
        server.shutdown()
        server.server_close()


def test_login_page_shows_bootstrap_credentials(tmp_path: Path) -> None:
    base, server = _start_server(tmp_path)
    try:
        page = urllib.request.urlopen(f"{base}/", timeout=5).read().decode("utf-8")
        assert "cosmos-admin" in page
        assert "COSMOS-Dev-2026!" in page
        assert "cosmos-background.css" in page
        login_js = (
            urllib.request.urlopen(f"{base}/assets/login.js", timeout=5)
            .read()
            .decode("utf-8")
        )
        assert 'selectedProfile: "ADMIN"' in login_js
    finally:
        server.shutdown()
        server.server_close()


def test_hub_scroll_layout_and_sidebar_is_live(tmp_path: Path) -> None:
    base, server = _start_server(tmp_path)
    opener = _client()
    try:
        _json(
            opener,
            f"{base}/api/auth/login",
            {
                "login_id": "cosmos-admin",
                "password": "COSMOS-Dev-2026!",
                "login_profile": "ADMIN",
            },
            method="POST",
        )
        hub = opener.open(f"{base}/app/workbenches", timeout=5).read().decode("utf-8")
        assert 'id="hub-pms"' in hub
        assert 'id="hub-workbench-lanes"' in hub
        assert 'id="carousel-viewport"' not in hub
        assert 'id="maharshi-module"' not in hub
        app_js = opener.open(f"{base}/assets/app.js", timeout=5).read().decode("utf-8")
        assert "window.COSMOS = COSMOS" in app_js
        assert "renderHubWorkbenchLanes" in app_js
        assert 'label: "Rocket Engine"' in app_js
        assert 'fab.id = "maharshi-module"' not in app_js
        maharshi_js = (
            opener.open(f"{base}/assets/maharshi-popup.js", timeout=5)
            .read()
            .decode("utf-8")
        )
        assert "mountMaharshiDock" in maharshi_js
        tokens = (
            opener.open(f"{base}/assets/cosmos-tokens.css", timeout=5)
            .read()
            .decode("utf-8")
        )
        assert "Inter" in tokens
        assert "IBM Plex Mono" in tokens

        planned = (
            opener.open(f"{base}/app/workbench/turbopumps", timeout=5)
            .read()
            .decode("utf-8")
        )
        assert "alert(" not in planned

        physics = opener.open(f"{base}/app/physics/compressible", timeout=5)
        assert "rocket-engine" in physics.geturl()
        assert "stage=nozzle" in physics.geturl()

        knowledge = (
            opener.open(f"{base}/app/workbench/knowledge", timeout=5)
            .read()
            .decode("utf-8")
        )
        assert "mh-diagnostics" in knowledge
        assert "Knowledge chat" in knowledge
    finally:
        server.shutdown()
        server.server_close()
