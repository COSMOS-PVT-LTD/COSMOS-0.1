"""Actual local HTTP baseline; exact comparison, excluding identity/time metadata only."""
import hashlib
import json
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http import cookiejar
from http.server import HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from gui.server import CosmosApplication, CosmosApplicationHandler  # noqa: E402

VOLATILE = {"design_id", "created_at", "updated_at", "timestamp", "computed_at", "run_id", "result_id", "last_updated", "generated_at", "performance_result_id", "consistency_result_id", "summary_result_id"}


def stable(value):
    if isinstance(value, dict):
        return {k: stable(v) for k, v in value.items() if k not in VOLATILE}
    if isinstance(value, list):
        return [stable(v) for v in value]
    return value


def run():
    with tempfile.TemporaryDirectory(prefix="cosmos-p05-parity-") as directory:
        class Handler(CosmosApplicationHandler):
            application = CosmosApplication(Path(directory), new_shell=True)
            def log_message(self, *_args):
                pass
        server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_port}"
        client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar.CookieJar()))
        def request(path, body=None):
            req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            try:
                response = client.open(req, timeout=30)
            except urllib.error.HTTPError as error:
                response = error
            return json.loads(response.read())
        try:
            request("/api/auth/login", {"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!", "login_profile": "ADMIN"})
            created = request("/api/propulsion/designs", {"name": "P05 parity fixture"})
            design_id = created["design"]["design_id"]
            prefix = f"/api/propulsion/designs/{design_id}"
            request(prefix + "/requirements", {"updates": {"target_chamber_pressure": {"magnitude": 50, "unit_symbol": "bar"}, "target_thrust": {"magnitude": 10, "unit_symbol": "kN"}, "mixture_ratio": 2.3, "expansion_ratio": 8, "ambient_pressure": {"magnitude": 101325, "unit_symbol": "Pa"}}})
            request(prefix + "/propellants", {"oxidizer_id": "LOX", "fuel_id": "RP1", "mixture_ratio": 2.3})
            phase3 = {"chamber_temperature_k": 3000, "gamma": 1.2, "molecular_weight_kg_per_mol": 0.022, "throat_area_m2": 0.01, "expansion_ratio": 8}
            phase4 = {"characteristic_length_m": 1, "contraction_ratio": 2.5, "wall_thickness_m": 0.006, "material_id": "stainless_304", "external_pressure_pa": 0, "external_pressure_source": "P05 explicit vacuum boundary", "material_temperature_k": 300, "viscosity_pa_s": 8e-5, "conductivity_w_m_k": 0.3, "cp_j_kg_k": 2500, "wall_temperature_k": 800}
            responses = {"phase3": request(prefix + "/run/phase3", phase3), "phase4": request(prefix + "/run/phase4", phase4), "phase6": request(prefix + "/run/phase6", {})}
            request(prefix + "/requirements", {"updates": {"target_chamber_pressure": {"magnitude": 55, "unit_symbol": "bar"}}})
            responses["stale"] = request(prefix + "/workflow")
            responses["invalid"] = request(prefix + "/propellants", {"oxidizer_id": "unknown", "fuel_id": "RP1", "mixture_ratio": 2.3})
            assert responses["phase3"]["stages"]["performance"]["status"] == "CURRENT"
            assert responses["phase6"]["stages"]["design_review"]["outputs"]["review_verdict"] == "INCOMPLETE"
            assert responses["invalid"]["ok"] is False
            return {"inputs": {"phase3": phase3, "phase4": phase4}, "responses": stable(responses), "excludedMetadataKeys": sorted(VOLATILE)}
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    baseline = HERE / "physics_before.json"
    result = run()
    if sys.argv[1:] == ["capture"]:
        assert not baseline.exists()
        baseline.write_text(json.dumps(result, indent=2) + "\n")
        print("Captured five actual HTTP scientific cases; assumed-state, not physical validation")
    else:
        (HERE / "physics_after.json").write_text(json.dumps(result, indent=2) + "\n")
        before = json.loads(baseline.read_text())
        equal = before == result
        report = {"pass": equal, "cases": 5, "comparison": "exact", "numericalTolerance": 0, "excludedMetadataKeys": sorted(VOLATILE), "baselineSHA256": hashlib.sha256(baseline.read_bytes()).hexdigest(), "physicalValidationClaimed": False}
        (HERE / "physics_parity.json").write_text(json.dumps(report, indent=2) + "\n")
        assert equal, "Scientific response regression: inspect physics_before/after.json"
        print("Physics parity PASS: five HTTP cases, exact comparison, no tolerance")
