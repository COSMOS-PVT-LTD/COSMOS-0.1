"""Capture a bounded NIST methane study surface and independent off-grid checks.

Never installs engine inputs, widens a live property record or opens owner data.
Predeclared interpolation checks are software checks, not physical validation.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, fields
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode

from core.quantity import Quantity
from core.unit import SI
from physics.fluids.liquid_table import LIQUID_TABLE, LiquidState
from scripts.prepare_methalox_thermal_envelope import saturation_states
from systems.propellants.nist_liquid import isobar, liquid_table


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saturation-study",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();out.mkdir(mode=0o700,parents=True,exist_ok=False)
    source=json.loads((args.saturation_study/"thermal-envelope-study.json").read_bytes())["nist"]["saturation"]
    raw=(args.saturation_study/source["raw_file"]).read_bytes()
    if sha256(raw).hexdigest()!=source["sha256"] or "ID=C74828" not in source["url"] or "RefState=DEF" not in source["url"]:
        raise ValueError("Retained same-fluid/common-reference saturation evidence required")
    saturation=saturation_states(raw)
    # Separate bounded numerical study domain, NOT user-approved engine inputs.
    ts=tuple(111.15+i for i in range(23));ps=tuple(500000.+i*50000 for i in range(7))
    check_ts=tuple(111.65+i for i in range(22));check_ps=tuple(525000.+i*50000 for i in range(6))
    ceiling={f.name:(5. if f.name=="enthalpy_j_kg" else .001) for f in fields(LiquidState)}
    declaration={"scope":"PROVISIONAL_PROPERTY_INTERPOLATION_STUDY_NOT_INSTALLED_ENGINE_INPUTS",
        "temperatures_k":ts,"pressures_pa":ps,"independent_check_temperatures_k":check_ts,"independent_check_pressures_pa":check_ps,
        "predeclared_error_ceilings":ceiling,"error_units":"enthalpy absolute J/kg; all other properties relative",
        "physical_validation":"NOT_PERFORMED","installed":False}
    def save(name,value):
        with (out/name).open("x") as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write("\n")
    save("predeclared-study.json",declaration)
    common={"Action":"Data","Wide":"on","ID":"C74828","Digits":8,"RefState":"DEF","TUnit":"K","PUnit":"bar",
            "DUnit":"kg/m3","HUnit":"kJ/kg","WUnit":"m/s","VisUnit":"Pa*s","STUnit":"N/m","Type":"IsoBar"}
    jobs=[("grid",p,ts) for p in ps]+[("off-grid",p,check_ts) for p in check_ps]
    def capture(job):
        kind,p,temps=job
        url="https://webbook.nist.gov/cgi/fluid.cgi?"+urlencode(common|{"P":p/1e5,"TLow":temps[0],"THigh":temps[-1],"TInc":1})
        received=subprocess.run(["curl","--http1.1","--fail","--silent","--show-error","--retry","2","--retry-all-errors","--retry-delay","1","--max-time","15",url],capture_output=True,check=False)
        if received.returncode:
            save(kind+"-"+str(int(p))+"Pa-request-failure.json",{"url":url,"curl_returncode":received.returncode,"stderr":received.stderr.decode(errors="replace")})
            raise ValueError("NIST source unavailable; request diagnostics retained, no invented property fallback")
        response=received.stdout
        filename=kind+"-"+str(int(p))+"Pa.tsv"
        with (out/filename).open("xb") as stream:stream.write(response)
        parsed=isobar(response,url,fluid_id="LCH4",temperatures_k=temps,pressure_pa=p)
        return {"kind":kind,"pressure_pa":p,"url":url,"raw_file":filename,"sha256":sha256(response).hexdigest(),"tls_verified":True},response,parsed
    with ThreadPoolExecutor(max_workers=3) as pool:captures=list(pool.map(capture,jobs))
    table=liquid_table(fluid_id="LCH4",temperatures_k=ts,pressures_pa=ps,
        responses=tuple((m["url"],r) for m,r,_ in captures if m["kind"]=="grid"),
        lowest_saturation_temperature_k=min(s["temperature_k"] for s in saturation),saturation_sha256=source["sha256"])
    save("liquid-table.json",asdict(table));save("source-manifest.json",{"isobars":[m for m,_,_ in captures],"saturation":source})
    errors=[]
    for manifest,_,states in captures:
        if manifest["kind"]!="off-grid":continue
        for t,reference in zip(check_ts,states,strict=True):
            actual=table.evaluate(Quantity(t,SI.get("K")),Quantity(manifest["pressure_pa"],SI.get("Pa")))
            error={f.name:abs(getattr(actual,f.name)-getattr(reference,f.name))/(1 if f.name=="enthalpy_j_kg" else abs(getattr(reference,f.name))) for f in fields(LiquidState)}
            errors.append({"temperature_k":t,"pressure_pa":manifest["pressure_pa"],"errors":error,"pass":all(error[k]<=v for k,v in ceiling.items())})
    report={"declaration":declaration,"model":LIQUID_TABLE.to_canonical_dict(),"checks":errors,
        "maximum_errors":{f.name:max(row["errors"][f.name] for row in errors) for f in fields(LiquidState)},
        "software_interpolation_pass":all(row["pass"] for row in errors),
        "limitations":["Off-grid agreement with NIST is not experimental validation or a certified uniform interpolation error bound.",
                       "No boiling or extrapolation; entire domain below lowest sourced saturation temperature.",
                       "No engine heat load, cooling feasibility or material allowable established."]}
    save("interpolation-check.json",report)
    print(json.dumps({"software_interpolation_pass":report["software_interpolation_pass"],"checks":len(errors),"maximum_errors":report["maximum_errors"],"installed":False}))
    if not report["software_interpolation_pass"]:raise ValueError("Predeclared interpolation ceilings failed; preserve evidence, refine in a NEW study")


if __name__=="__main__":main()
