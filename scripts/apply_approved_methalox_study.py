"""Create a labelled managed study clone using the normal loopback HTTP API.

Never overwrite the original design or choose missing engineering inputs.
Requires the exact source commit, prepared approval-bound input document, and
explicit local-development login flag. No migration, force write or hardware claim.
"""
from __future__ import annotations

import argparse
import json
import math
from hashlib import sha256
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4

from prepare_approved_methalox_study import APPROVAL, read_state


def validate_approved(spec: dict, folder: Path) -> None:
    """Reject altered assumptions or a config detached from its retained NIST rows."""
    if (spec["schema"] != "cosmos.approved-preliminary-methalox-study.v1"
        or spec["requirements"] != {"burn_duration": {"magnitude": 5, "unit_symbol": "s"}}
        or spec["regulated_source_pressure_absolute_pa_each"] != 800000
        or spec["material_candidates_only"] != {"liner": "GRCop-42", "jacket": "INCONEL 718"}
        or set(spec["subsystem_inputs"]) != {"injector"}):
        raise ValueError("Prepared inputs differ from the approved study scope")
    cfg = spec["subsystem_inputs"]["injector"]
    expected_keys = {"property_source"}
    for name, temperature in (("fuel", 111.15), ("oxidizer", 90.15)):
        state = spec["nist_states"][name]["6"]
        # A local exact sibling filename, never a caller-controlled arbitrary path.
        raw = (folder / f"{name}-nist-6bar.tsv").read_bytes()
        if sha256(raw).hexdigest() != state["sha256"]:
            raise ValueError("Retained NIST response hash mismatch")
        actual = read_state(raw, pressure_bar=6, temperature_k=temperature)["properties_si"]
        values = {"pressure_drop_pa": 100000, "cd": .7, "hole_count": 8,
                  "density_kg_m3": actual["density_kg_m3"], "viscosity_pa_s": actual["viscosity_pa_s"]}
        for key, expected in values.items():
            key = f"{name}_{key}"
            expected_keys.add(key)
            if type(cfg[key]) not in (int, float) or cfg[key] != expected:
                raise ValueError("Injector config differs from approved assumptions/exact source state")
    if set(cfg) != expected_keys or not isinstance(cfg["property_source"], str) or not cfg["property_source"].strip():
        raise ValueError("Injector requires only the approved, sourced fields")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--design", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--development-login", action="store_true", required=True)
    args = parser.parse_args()
    parsed = urlparse(args.api)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.path not in ("", "/") or parsed.username:
        raise ValueError("Only explicit loopback local-development API is permitted")
    spec_bytes = args.inputs.read_bytes()
    spec = json.loads(spec_bytes)
    validate_approved(spec, args.inputs.parent)
    if spec["approval_record"]["sha256"] != sha256(APPROVAL.read_bytes()).hexdigest():
        raise ValueError("Approval record changed; prepare/review inputs again before applying")
    out = args.evidence.absolute()
    out.mkdir(parents=True, exist_ok=False, mode=0o700)
    client = build_opener(HTTPCookieProcessor(CookieJar()))

    def request(path, data=None):
        raw = None if data is None else json.dumps(data, allow_nan=False).encode()
        with client.open(Request(args.api.rstrip("/")+path, data=raw,
                                 headers={"Content-Type": "application/json"}), timeout=120) as response:
            result = json.load(response)
        if result.get("ok") is False:
            raise ValueError(result.get("error", "Managed API command failed; originals retained"))
        return result

    def save(name, value):
        (out/name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n")

    def command(envelope, **body):
        return {"expected": envelope["authority"]["head"], "operation_id": str(uuid4()), **body}

    request("/api/auth/login", {"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!", "login_profile": "ADMIN"})
    path = f"/api/projects/{args.project}/designs/{args.design}"
    original = request(path)
    if original["authority"]["commit_id"] != args.source_commit:
        raise ValueError("Source head changed; no study clone created. Read/review current source first")
    req, thermo = original["design"]["requirements"], original["design"]["thermochemistry_configuration"]

    def quantity(value):
        return value["magnitude"] * value["unit"]["factor_to_si"]

    basis = (quantity(req["target_thrust"]), quantity(req["target_chamber_pressure"]),
             quantity(req["ambient_pressure"]), req["mixture_ratio"], thermo["fuel_temperature_k"], thermo["oxidizer_temperature_k"])
    if not all(math.isclose(a, b, rel_tol=1e-12) for a, b in zip(basis, (1500, 500000, 101325, 2.633, 111.15, 90.15), strict=True)):
        raise ValueError("Source differs from approved methalox study basis")
    save("original-before.json", original)
    clone = request(path+"/clone", command(original, source_commit_id=args.source_commit,
                     name="Methalox 1.5 kN · approved cold study · NOT hardware ready"))
    save("clone-created.json", clone)
    clone_path = f"/api/projects/{args.project}/designs/{clone['authority']['object_id']}"
    notes = (req.get("notes") or "") + (
        "\n2026-10-21 approved PRELIMINARY study: duration5s; regulated source8bar absolute each; "
        "injector drop1bar each; Cd0.70; 8 ports per propellant. Cold injector properties at6bar "
        "absolute, CH4 111.15K / O2 90.15K, NIST calculated reference values, not engine measurements. "
        "GRCop-42 liner / INCONEL718 jacket are candidates only, NOT selected allowables. "
        "No heated feed/property window, line/control losses, cooling design or hardware approval inferred. "
        "Study inputs SHA256 " + sha256(spec_bytes).hexdigest())
    saved = request(clone_path+"/save", command(clone, base_revision=clone["design"]["revision"],
                    requirements={**spec["requirements"], "notes": notes}, subsystem_inputs=spec["subsystem_inputs"]))
    save("approved-input-envelope.json", saved)
    result = request(clone_path+"/run/analysis", command(saved, phase3_inputs={}, phase4_inputs={}))
    save("analysis-envelope.json", result)
    after = request(path)
    save("qualification.json", {"original_design_unchanged": original["source_canonical_json"] == after["source_canonical_json"],
         "input_document_sha256": sha256(spec_bytes).hexdigest(), "stages": {key: value["status"] for key, value in result["stages"].items()},
         "physical_validation": "NOT_PERFORMED", "goal_complete": False, "R08": "HOLD_UNTIL_USER_ACCEPTANCE"})
    assert original["source_canonical_json"] == after["source_canonical_json"]
    assert result["stages"]["injector"]["status"] == "CURRENT", "Inspect retained diagnostics; study clone preserved"
    assert result["execution_ok"] is True and result["workflow_complete"] is False
    print(json.dumps({"project": args.project, "design": result["authority"]["object_id"],
                      "commit": result["authority"]["commit_id"], "revision": result["design"]["revision"],
                      "phase_status": result["phase_status"], "original_unchanged": True}))


if __name__ == "__main__":
    main()
