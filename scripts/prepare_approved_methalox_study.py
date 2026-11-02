"""Prepare approved cold hydraulic study inputs; never open application storage.

Retain the draft, approvals, exact NIST states and raw response hashes separately.
This does not infer hot allowables, heated coolant properties or a feed solution.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
APPROVAL = ROOT / "docs/implementation/evidence/ENGINE_WORKFLOW_REPAIR_2026-10-21/PRELIMINARY_INPUT_PROPOSAL.md"


def read_state(raw: bytes, *, pressure_bar: float, temperature_k: float) -> dict:
    """Require exact requested state, SI transport units, liquid phase, no guesses."""
    table = list(csv.DictReader(io.StringIO(raw.decode("utf-8")), delimiter="\t"))
    rows = [row for row in table if float(row["Pressure (bar)"]) == pressure_bar
            and float(row["Temperature (K)"]) == temperature_k]
    if len(rows) != 1 or rows[0]["Phase"] != "liquid":
        raise ValueError("NIST must return one matching, explicitly liquid state")
    row = rows[0]
    # Cp conversion is explicit; all other consumed fields already use SI units.
    values = {"density_kg_m3": float(row["Density (kg/m3)"]),
              "viscosity_pa_s": float(row["Viscosity (Pa*s)"]),
              "cp_j_kg_k": 1000 * float(row["Cp (J/g*K)"]),
              "conductivity_w_m_k": float(row["Therm. Cond. (W/m*K)"])}
    import math
    if not all(math.isfinite(value) and value > 0 for value in values.values()):
        raise ValueError("Nonpositive or nonfinite NIST liquid properties")
    return {"raw_row": row, "properties_si": values,
            "state": {"temperature_k": temperature_k, "pressure_pa": pressure_bar * 100000}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.absolute()
    out.mkdir(parents=True, exist_ok=False, mode=0o700)
    approval = APPROVAL.read_bytes()
    if "Approve these preliminary study assumptions" not in approval.decode():
        raise ValueError("Expected explicit preliminary-study approval record")
    records = {}
    injector = {"fuel_pressure_drop_pa": 100000, "oxidizer_pressure_drop_pa": 100000,
                "fuel_cd": .7, "oxidizer_cd": .7, "fuel_hole_count": 8, "oxidizer_hole_count": 8}
    for name, cas, temperature in (("fuel", "C74828", 111.15), ("oxidizer", "C7782447", 90.15)):
        records[name] = {}
        for pressure in (6, 8):
            params = {"Action": "Data", "Wide": "on", "ID": cas, "Type": "IsoTherm", "Digits": 6,
                      "PLow": pressure, "PHigh": pressure + .1, "PInc": .1, "T": temperature,
                      "RefState": "DEF", "TUnit": "K", "PUnit": "bar", "DUnit": "kg/m3",
                      "HUnit": "kJ/kg", "WUnit": "m/s", "VisUnit": "Pa*s", "STUnit": "N/m"}
            url = "https://webbook.nist.gov/cgi/fluid.cgi?" + urlencode(params)
            raw = subprocess.run(["curl", "--fail", "--silent", "--show-error", "--max-time", "25", url],
                                 check=True, capture_output=True).stdout
            state = read_state(raw, pressure_bar=pressure, temperature_k=temperature)
            filename = f"{name}-nist-{pressure}bar.tsv"
            (out / filename).write_bytes(raw)
            state.update(url=url, sha256=sha256(raw).hexdigest(), raw_file=filename,
                         authority="NIST WebBook calculated reference-fluid properties, not engine measurements",
                         tls_verification=True)
            records[name][str(pressure)] = state
        props = records[name]["6"]["properties_si"]
        injector.update({f"{name}_density_kg_m3": props["density_kg_m3"],
                         f"{name}_viscosity_pa_s": props["viscosity_pa_s"]})
    injector["property_source"] = (
        "NIST WebBook liquid cold injector-manifold states at 6 bar absolute: CH4 111.15 K, O2 90.15 K. "
        "Raw URLs/SHA256: approved-study-inputs.json. No coolant preheating is assumed; heated feed is not qualified. "
        f"Fuel SHA256 {records['fuel']['6']['sha256']}; oxidizer SHA256 {records['oxidizer']['6']['sha256']}. "
        "Cd0.70 and 8 ports/propellant are user-approved exploratory assumptions (2026-10-21), not measured values."
    )
    payload = {"schema": "cosmos.approved-preliminary-methalox-study.v1",
               "approval_record": {"path": str(APPROVAL.relative_to(ROOT)), "sha256": sha256(approval).hexdigest(),
                                   "date": "2026-10-21", "response": "Approve these preliminary study assumptions"},
               "scope": "PRELIMINARY_COLD_HYDRAULIC_STUDY_NOT_HARDWARE_VALIDATION",
               "requirements": {"burn_duration": {"magnitude": 5, "unit_symbol": "s"}},
               "regulated_source_pressure_absolute_pa_each": 800000,
               "material_candidates_only": {"liner": "GRCop-42", "jacket": "INCONEL 718"},
               "subsystem_inputs": {"injector": injector}, "nist_states": records,
               "not_installed_or_inferred": ["Material selection/allowables", "Thermal wall temperature",
                   "Heated coolant property domain", "Cooling geometry", "Line/valve/control losses",
                   "Feed/operating-point closure", "Manufacturing/hardware approval"],
               "R08": "HOLD_UNTIL_USER_ACCEPTANCE"}
    (out / "approved-study-inputs.json").write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False)+"\n")
    print(json.dumps({"prepared": str(out / "approved-study-inputs.json"), "installed": False,
                      "injector_density_kg_m3": {name: records[name]["6"]["properties_si"]["density_kg_m3"] for name in records}}))


if __name__ == "__main__":
    main()
