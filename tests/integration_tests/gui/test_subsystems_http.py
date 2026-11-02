"""Authenticated HTTP subsystem execution using synthetic inputs."""

import json
import urllib.error

import pytest

from systems.persistence.design_store import DesignStore
from tests.fixtures.propulsion_subsystems import (
    cooling_inputs,
    film_inputs,
    injector_inputs,
    nozzle_inputs,
    seeded_design,
)
from tests.integration_tests.gui.test_propulsion_e2e_http import (
    _client,
    _json,
    _start_server,
)


def test_subsystems_http_roundtrip_and_fail_closed(tmp_path):
    design = seeded_design()
    DesignStore(tmp_path / "propulsion_designs").save(design)
    base, server = _start_server(tmp_path)
    client = _client()
    url = f"{base}/api/propulsion/designs/{design.design_id}/run/subsystems"
    try:
        with pytest.raises(urllib.error.HTTPError) as unauthenticated:
            _json(client, url, {}, "POST")
        assert unauthenticated.value.code == 401
        _json(
            client,
            f"{base}/api/auth/login",
            {
                "login_id": "cosmos-admin",
                "password": "COSMOS-Dev-2026!",
                "login_profile": "ADMIN",
            },
            "POST",
        )
        result = _json(
            client,
            url,
            {
                "inputs": {
                    "injector": injector_inputs(),
                    "nozzle": nozzle_inputs(),
                    "cooling": cooling_inputs() | film_inputs(),
                }
            },
            "POST",
        )
        assert result["execution_ok"] is True
        assert result["workflow_complete"] is False
        assert result["validation_level"] == "NOT_CLAIMED"
        reloaded = _json(client, f"{base}/api/propulsion/designs/{design.design_id}")[
            "design"
        ]
        assert reloaded["subsystem_inputs"]["cooling"]["film_mode"] == "gaseous_slot"
        assert reloaded["cooling_design"]["film_mass_flow_estimate_kg_s"] > 0
        invalid = _json(
            client,
            url,
            {
                "stages": ["cooling"],
                "inputs": {"cooling": cooling_inputs() | {"channel_count": 10000}},
            },
            "POST",
        )
        assert invalid["execution_ok"] is False
        assert invalid["stages"]["cooling"]["status"] == "OUT_OF_RANGE"
        exported = _json(
            client, f"{base}/api/propulsion/designs/{design.design_id}/export"
        )["package"]
        assert "cooling" not in exported["current_results"]
        before = _json(client, f"{base}/api/propulsion/designs/{design.design_id}")[
            "design"
        ]["revision"]
        for payload in (
            {"stages": ["cycle"]},
            {"stages": "cooling"},
            {"inputs": {"cooling": {"channel_count": True}}},
        ):
            with pytest.raises(urllib.error.HTTPError) as malformed:
                _json(client, url, payload, "POST")
            assert malformed.value.code == 400
            assert json.loads(malformed.value.read())["ok"] is False
        assert (
            _json(client, f"{base}/api/propulsion/designs/{design.design_id}")[
                "design"
            ]["revision"]
            == before
        )
    finally:
        server.shutdown()
        server.server_close()
