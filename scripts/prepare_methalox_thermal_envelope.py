"""Retain exact NIST saturation evidence and CAD coolant metrics; never edit live data.

This is a nominal 8bar/111.15K methane bulk heating bound, not a cooling solution,
temperature window, material selection or installed engineering input set.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import subprocess
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode

from core.quantity import Quantity
from core.unit import SI
from physics.heat_transfer.liquid_budget import (
    LIQUID_HEATING_THRESHOLD,
    liquid_heating_threshold,
)
from physics.si import UNIT_SPECIFIC_ENERGY
from systems.contracts.geometry import DesignSnapshot, GeometryFeatureGraph
from systems.geometry.component_cooling import geometry_handoff
from systems.geometry.component_model import from_contracts


def saturation_states(raw: bytes) -> list[dict]:
    """Reject the wrong NIST saturation type, units, duplicates and missing rows."""
    reader = csv.DictReader(io.StringIO(raw.decode()), delimiter="\t")
    rows = list(reader)
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames) or any(None in r or None in r.values() for r in rows):
        raise ValueError("Malformed/ambiguous NIST saturation table columns")
    if len(rows) != 4 or [float(r["Pressure (bar)"]) for r in rows] != [5., 6., 7., 8.]:
        raise ValueError("Require exactly the requested four saturation-pressure states, not a temperature grid")
    result = []
    for row in rows:
        t, p, rho = (float(row[k]) for k in ("Temperature (K)", "Pressure (bar)", "Density (l, kg/m3)"))
        hl, hv = (1000 * float(row[k]) for k in ("Enthalpy (l, kJ/kg)", "Enthalpy (v, kJ/kg)"))
        if not all(math.isfinite(v) for v in (t, p, rho, hl, hv)) or min(t, p, rho) <= 0 or hv <= hl:
            raise ValueError("NIST saturation states must be finite and retain distinct liquid/vapour branches")
        result.append({"temperature_k": t, "pressure_pa": 100000 * p,
                       "saturated_liquid_enthalpy_j_kg": hl, "saturated_vapour_enthalpy_j_kg": hv})
    return result


def inlet_enthalpy(raw: bytes) -> float:
    reader = csv.DictReader(io.StringIO(raw.decode()), delimiter="\t")
    rows = list(reader)
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames) or any(None in r or None in r.values() for r in rows):
        raise ValueError("Malformed/ambiguous NIST inlet table columns")
    matching = [r for r in rows if float(r["Temperature (K)"]) == 111.15 and float(r["Pressure (bar)"]) == 8.]
    if len(matching) != 1 or matching[0]["Phase"] != "liquid":
        raise ValueError("Require one exact 8bar/111.15K liquid methane inlet")
    h = 1000 * float(matching[0]["Enthalpy (kJ/kg)"])
    if not math.isfinite(h):
        raise ValueError("Inlet enthalpy must be finite")
    return h


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembly", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    baseline_raw = (args.assembly / "engine-baseline.json").read_bytes()
    model_raw = (args.assembly / "model-envelope.json").read_bytes()
    baseline, model = json.loads(baseline_raw), json.loads(model_raw)
    design = json.loads(baseline["source_canonical_json"])
    if model["model"]["baseline_commit_id"] != baseline["authority"]["commit_id"]:
        raise ValueError("CAD and retained engine baseline must be exactly bound")
    if "approved cold study" not in design["name"]:
        raise ValueError("Use the separate approved cold-study source, not an unapproved case")
    if design["propellant_configuration"]["fuel_id"] != "LCH4" or design["propellant_configuration"]["oxidizer_id"] != "LOX":
        raise ValueError("This NIST evidence is specific to liquid methane / LOX, not another propellant pair")
    if model["model"]["baseline_canonical_json"] != baseline["source_canonical_json"]:
        raise ValueError("Retained model must bind the exact canonical engine payload")
    thermo, req = design["thermochemistry_configuration"], design["requirements"]
    if thermo["fuel_temperature_k"] != 111.15 or thermo["oxidizer_temperature_k"] != 90.15:
        raise ValueError("This study is specifically for the approved cryogenic inlet states")
    for key, expected in (("target_thrust",1500.), ("target_chamber_pressure",500000.), ("burn_duration",5.)):
        if not math.isclose(Quantity.from_canonical_dict(req[key]).to_si(), expected, rel_tol=1e-12):
            raise ValueError("This study must retain the approved nominal thrust/pressure/duration")
    injector = design["workflow"]["results"]["injector"]
    if injector["status"] != "CURRENT" or injector["model_id"] != "PHYS-INJ.liquid_orifice":
        raise ValueError("Exact retained CURRENT liquid injector hydraulics required")
    fuel = injector["outputs"]["fuel"]["mass_flow_kg_s"]
    out = args.output.absolute(); out.mkdir(parents=True, exist_ok=False, mode=0o700)
    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    common = {"Action":"Data", "Wide":"on", "ID":"C74828", "Digits":8, "RefState":"DEF",
              "TUnit":"K", "PUnit":"bar", "DUnit":"kg/m3", "HUnit":"kJ/kg", "WUnit":"m/s", "VisUnit":"Pa*s", "STUnit":"N/m"}
    sources = {}
    for name, params in (("saturation", {"Type":"SatT", "PLow":5, "PHigh":8, "PInc":1}),
                         ("inlet", {"Type":"IsoTherm", "T":111.15, "PLow":8, "PHigh":8.1, "PInc":.1})):
        url = "https://webbook.nist.gov/cgi/fluid.cgi?" + urlencode({**common, **params})
        raw = subprocess.run(["curl", "--fail", "--silent", "--show-error", "--max-time", "30", url], capture_output=True, check=True).stdout
        parsed = saturation_states(raw) if name == "saturation" else inlet_enthalpy(raw)
        filename = "methane-nist-" + name + ".tsv"
        (out / filename).write_bytes(raw)
        sources[name] = {"url":url, "sha256":sha256(raw).hexdigest(), "raw_file":filename, "parsed":parsed,
                         "reference":"NIST DEF for the same methane fluid; kJ/kg converted explicitly to J/kg", "tls_verified":True}
    thresholds = []
    for row in sources["saturation"]["parsed"]:
        result = liquid_heating_threshold(mass_flow=Quantity(fuel, SI.get("kg/s")),
            inlet_enthalpy=Quantity(sources["inlet"]["parsed"], UNIT_SPECIFIC_ENERGY),
            saturated_liquid_enthalpy=Quantity(row["saturated_liquid_enthalpy_j_kg"], UNIT_SPECIFIC_ENERGY),
            duration=Quantity(5, SI.get("s")))
        thresholds.append({**row, **asdict(result)})
    handoff = geometry_handoff(from_contracts(DesignSnapshot.from_json(model["model"]["snapshot_json"]), GeometryFeatureGraph.from_json(model["model"]["graph_json"])))
    save("coolant-geometry-handoff.json", {**handoff, "model_authority":model["authority"], "baseline_authority":baseline["authority"],
         "currentness":"CAPTURED_SOURCE_ONLY_NOT_A_LIVE_CURRENTNESS_CLAIM"})
    report = {"schema":"cosmos.methalox-thermal-envelope-study.v1", "installed":False,
              "physics_model":LIQUID_HEATING_THRESHOLD.to_canonical_dict(),
              "source_authority":baseline["authority"], "model_authority":model["authority"],
              "source_file_sha256":{"engine_baseline":sha256(baseline_raw).hexdigest(), "model_envelope":sha256(model_raw).hexdigest()},
              "fuel_mass_flow_kg_s":fuel, "duration_s":5, "nist":sources, "thresholds":thresholds,
              "interpretation":"Nominal steady bulk-saturation energy thresholds, not allowable heat loads or a cooling/engine solution",
              "not_established":["Actual coolant pressure path", "Gas-side heat load", "Wall boiling onset", "Heated-injector properties",
                                 "Material/process-specific strength", "Full chamber/convergent/nozzle thermal coverage", "Physical validation"],
              "R08":"HOLD_UNTIL_USER_ACCEPTANCE"}
    save("thermal-envelope-study.json", report)
    print(json.dumps({"study":str(out), "installed":False, "fuel_mass_flow_kg_s":fuel,
                      "thresholds":[{"pressure_pa":r["pressure_pa"], "saturation_temperature_k":r["temperature_k"], "bulk_saturation_onset_heat_w":r["saturation_onset_heat_w"]} for r in thresholds]}, allow_nan=False))


if __name__ == "__main__":
    main()
