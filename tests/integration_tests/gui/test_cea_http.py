"""Authenticated HTTP uses native CEA and saves the same design and provenance."""

import urllib.error

import pytest

from physics.exceptions import ThermochemistryError
from tests.integration_tests.gui.test_propulsion_e2e_http import (
    _client,
    _json,
    _start_server,
)
from tests.unit_tests.api.test_cea_workflow import CONFIG


def test_cea_http_native_save_reload_invalidate_and_failure(tmp_path, monkeypatch):
    pytest.importorskip("cea")
    base, server = _start_server(tmp_path)
    client = _client()
    try:
        _json(client, f"{base}/api/auth/login", {"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!",
                                               "login_profile": "ADMIN"}, "POST")
        design = _json(client, f"{base}/api/propulsion/designs", {"name": "HTTP CEA regression"}, "POST")["design"]
        url = f"{base}/api/propulsion/designs/{design['design_id']}"
        _json(client, url + "/requirements", {"target_chamber_pressure": 5e5, "ambient_pressure": 0,
                                              "mixture_ratio": 2.7239, "expansion_ratio": 10,
                                              "propellant_selection": "LOX/LCH4"}, "POST")
        payload = {"thermochemistry_configuration": CONFIG, "throat_area_m2": .001}
        with pytest.raises(urllib.error.HTTPError) as unauthenticated:
            _json(_client(), url + "/run/phase3", payload, "POST")
        assert unauthenticated.value.code == 401
        result = _json(client, url + "/run/phase3", payload, "POST")
        assert result["execution_ok"]
        reloaded = _json(client, url)["design"]
        assert reloaded["thermochemistry_configuration"] == CONFIG
        assert reloaded["workflow"]["results"]["thermochemistry"]["outputs"]["engine_provenance"]["converged"]
        def failed(*args, **kwargs):
            raise ThermochemistryError("Native nonconvergence regression")
        monkeypatch.setattr("plugins.nasa_cea.engine.NasaCeaEngine.evaluate", failed)
        failure = _json(client, url + "/run/phase3", payload, "POST")
        assert not failure["execution_ok"]
        assert failure["stages"]["thermochemistry"]["status"] == "FAILED"
        assert failure["stages"]["performance"]["status"] == "FAILED"
        exported = _json(client, url + "/export")["package"]
        assert "performance" not in exported["current_results"]
        with pytest.raises(urllib.error.HTTPError) as mixed:
            _json(client, url + "/run/phase3", payload | {"gamma": 1.2}, "POST")
        assert mixed.value.code == 400
    finally:
        server.shutdown()
        server.server_close()
