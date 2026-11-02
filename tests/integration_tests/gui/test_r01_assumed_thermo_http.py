"""HTTP assumed-state validation uses private pytest storage, not user designs."""

import pytest

from tests.integration_tests.gui.test_propulsion_e2e_http import (
    _client,
    _json,
    _start_server,
)


@pytest.mark.parametrize("field,value", [
    ("gamma", .5), ("gamma", "nan"), ("chamber_temperature_k", 0.),
    ("chamber_temperature_k", "inf"), ("molecular_weight_kg_per_mol", 0.),
    ("molecular_weight_kg_per_mol", "nan"),
])
def test_http_invalid_assumptions_preserve_valid_operating_point_and_fail_closed(tmp_path, field, value):
    base, server = _start_server(tmp_path)
    client = _client()
    try:
        _json(client, base + "/api/auth/login", {"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!",
                                                "login_profile": "ADMIN"}, "POST")
        design = _json(client, base + "/api/propulsion/designs", {"name": "R01C synthetic HTTP validation"}, "POST")["design"]
        url = base + "/api/propulsion/designs/" + design["design_id"]
        _json(client, url + "/requirements", {"target_chamber_pressure": 3e6, "ambient_pressure": 101325,
            "mixture_ratio": 2.5, "expansion_ratio": 10., "propellant_selection": "LOX/RP-1"}, "POST")
        valid = {"chamber_temperature_k": 3500., "gamma": 1.2, "molecular_weight_kg_per_mol": .025,
                 "throat_area_m2": .001, "expansion_ratio": 10.}
        assert _json(client, url + "/run/phase3", valid, "POST")["execution_ok"]
        before = _json(client, url)["design"]["operating_point"]
        failed = _json(client, url + "/run/phase3", valid | {field: value}, "POST")
        assert not failed["execution_ok"]
        for stage in ("operating_point", "thermochemistry", "performance"):
            assert failed["stages"][stage]["status"] == "FAILED"
        after = _json(client, url)["design"]
        assert after["operating_point"] == before
        assert "performance" not in _json(client, url + "/export")["package"]["current_results"]
    finally:
        server.shutdown()
        server.server_close()
