#!/usr/bin/env python3
"""Read public NIST data; prepare an UNAPPROVED numerical-study proposal.

No application root is opened. No proposed inputs are installed or accepted.
Secure system curl keeps normal TLS validation (the local Python CA store is
unconfigured); a transfer/parse/phase error stops, never substitutes constants.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core.quantity import Quantity
from core.unit import SI
from physics.injectors.orifice import liquid_orifice
from physics.si import UNIT_DYNAMIC_VISCOSITY


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(); root=args.output.absolute(); root.mkdir(parents=True,exist_ok=False,mode=0o700)
    rows={}; sources={}
    for name,cas,temp in (("fuel","C74828",111.15),("oxidizer","C7782447",90.15)):
        params={"Action":"Data","Wide":"on","ID":cas,"Type":"IsoTherm","Digits":6,
            "PLow":8,"PHigh":8.1,"PInc":.1,"T":temp,"RefState":"DEF","TUnit":"K",
            "PUnit":"bar","DUnit":"kg/m3","HUnit":"kJ/kg","WUnit":"m/s","VisUnit":"Pa*s","STUnit":"N/m"}
        url="https://webbook.nist.gov/cgi/fluid.cgi?"+urlencode(params)
        raw=subprocess.run(["curl","--fail","--silent","--show-error","--max-time","25",url],check=True,capture_output=True).stdout
        table=list(csv.DictReader(io.StringIO(raw.decode()),delimiter="\t"))
        row=next(r for r in table if float(r["Pressure (bar)"])==8)
        if row["Phase"]!="liquid" or float(row["Temperature (K)"])!=temp:
            raise ValueError("NIST returned a different phase or state")
        (root/(name+"-nist-8bar.tsv")).write_bytes(raw)
        rows[name]=row;sources[name]={"url":url,"sha256":sha256(raw).hexdigest(),"state":{"temperature_k":temp,"pressure_pa":800000},"authority":"NIST WebBook fluid-property calculation, not measurements of this engine","tls_verification":True}
    case=json.loads((ROOT/"output/methalox-1500N-5bar-2026-10-21-v3/cea-study.json").read_text())["selected"]
    hydraulics={}
    for name,flow in (("fuel",case["fuel_flow_kg_s"]),("oxidizer",case["oxidizer_flow_kg_s"])):
        row=rows[name]
        hydraulics[name]=asdict(liquid_orifice(Quantity(flow,SI.get("kg/s")),Quantity(float(row["Density (kg/m3)"]),SI.get("kg/m3")),
            Quantity(100000,SI.get("Pa")),Quantity(float(row["Viscosity (Pa*s)"]),UNIT_DYNAMIC_VISCOSITY),.7,8))
    proposal={"status":"DRAFT_REQUIRES_USER_APPROVAL_NOT_INSTALLED", "physical_validation":"NOT_PERFORMED",
        "purpose":"Preliminary steady numerical and geometry development only; no hardware/test authorization",
        "unchanged_user_requirements":{"target_thrust_n":1500,"chamber_pressure_absolute_pa":500000,"ambient_pressure_pa":101325,
            "fuel_temperature_k":111.15,"oxidizer_temperature_k":90.15,"cycle_type":"PRESSURE_FED"},
        "proposed_assumptions":{"burn_duration_s":5,"regulated_tank_pressure_absolute_pa":800000,
            "injector_pressure_drop_pa_each":100000,"injector_cd_each":.7,"holes_per_propellant":8,
            "basis":"Explicit exploratory engineering choices, not measured Cd/losses, certified limits, NASA recommendations or derived safe operating settings. Burn duration does not validate startup/transient loads."},
        "property_sources":sources,"nist_state_rows":rows,"preliminary_orifice_results":hydraulics,
        "material_candidates":[{"role":"high-conductivity liner candidate","material":"GRCop-42",
            "source":"https://ntrs.nasa.gov/citations/20190030433","status":"Candidate only. Exact process/heat-treatment-dependent properties and applicability must be ingested/verified before a thermal/stress result; no universal allowable inferred."},
            {"role":"outer structural jacket candidate","material":"INCONEL 718","source":"https://www.specialmetals.com/documents/technical-bulletins/inconel/inconel-alloy-718.pdf",
            "status":"Candidate only. Manufacturer tables depend on product form and heat treatment; not automatic engine qualification or catalog substitution."}],
        "not_executable_as_full_engine_input_yet":["Single NIST liquid state is not a temperature/pressure applicability window, saturation model or heated-coolant dataset.",
            "Full chamber/convergent cooling and a matched channel/thermal topology remain to be implemented and qualified.",
            "Current illustrative doublet CAD has equal bores; proposed fuel/oxidizer hydraulic diameters differ. Separate port identity/radii and feed routing must be implemented, not hidden.",
            "Existing tensile thin-wall model does not cover the concept wall radius/thickness ratio below10 or internally cooled ligaments. Appropriate structural models and material data remain necessary.",
            "No tank/manifold/line control losses or feed resistance are accepted from these assumptions. Independent feed closure, phase/cavitation and pressure budget checks remain necessary."]}
    (root/"proposal.json").write_text(json.dumps(proposal,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"proposal":str(root/"proposal.json"),"density_kg_m3":{name:float(row["Density (kg/m3)"]) for name,row in rows.items()},
        "preliminary_bore_diameter_mm":{name:row["diameter_m"]*1000 for name,row in hydraulics.items()},"approved":False}))


if __name__=="__main__":
    main()
