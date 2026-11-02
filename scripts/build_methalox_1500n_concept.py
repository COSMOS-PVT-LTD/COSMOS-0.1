#!/usr/bin/env python3
"""User-authorized preliminary study and native CAD; never hardware acceptance.

Uses existing Physics/Systems/managed-project/native-worker boundaries. Outputs
go to a NEW isolated root, not the owner's live cosmos_app_data. No migrations,
synthetic reviewers, material properties, coolant performance or release claims.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.project_authority import principal
from api.propulsion_workflow import (
    create_design, run_phase3, update_cycle, update_propellants, update_requirements,
)
from gui.server import CosmosApplication
from physics.compressible_flow.external_nozzle import scale_external_nozzle
from physics.quantities import pascal, quantity, square_metre
from core.unit import SI
from physics.thermochemistry.cea_interface import CeaRequest, run_thermochemistry
from physics.exceptions import ThermochemistryError
from plugins.nasa_cea import bind_nasa_cea_engine
from systems.configuration.subsystems import configure_subsystems
from systems.geometry.component_model import compile_model
from systems.projects.authority import Head
from systems.stages.chamber import run_chamber_stage
from systems.stages.nozzle import run_nozzle_stage

PC, PA, TARGET = 500_000.0, 101_325.0, 1500.0
TF, TO = 111.15, 90.15
RUNTIME = ROOT / "docs/implementation/evidence/R07_COMPONENTS_2026-10-20/runtime-qualified-v3.json"
ASSUMPTIONS = {
    "ambient_pressure_pa": {"value": PA, "basis": "Conventional standard sea-level static pressure; not measured weather."},
    "chemistry": "NASA CEA 3.3.4 infinite-area combustor, equilibrium ideal nozzle. Frozen expansion is sensitivity only.",
    "selection": "Maximum ideal sea-level Isp on explicit O/F grid 1.5..4.5 in 0.05 steps, refined +/-0.05 in 0.001 steps; exit pressure matched to ambient per point. Finite-grid theoretical selection, not a global hardware optimum.",
    "efficiencies": "No combustion, discharge, viscous, divergence, cooling, heat-loss or separation efficiency correction; 1500 N is ideal modeled thrust, NOT predicted delivered hardware thrust.",
    "characteristic_length_m": {"value": 0.8, "basis": "Provisional concept choice, not methane residence-time/stability qualification. Existing cylindrical L* sizing excludes convergent volume."},
    "contraction_ratio": {"value": 3.0, "basis": "Provisional Ac/At; not a finite-area combustion correction."},
    "contour": {"length_fraction": 0.8, "start_angle_deg": 30.0, "exit_angle_deg": 8.0, "blend_radius_ratio": 0.2, "point_count": 41, "basis": "Provisional monotone tangent bell; not Rao optimum/MOC. CAD retains all 41 source stations as piecewise-linear profile."},
    "wall_thickness_m": {"value": 0.006, "basis": "Radial CAD thickness only; no material, structural or thermal acceptance."},
    "convergent_length_m": {"value": 0.045, "basis": "Straight provisional convergent; junctions are not manufacturing blends."},
    "throat_land_length_m": {"value": 0.003, "basis": "Provisional straight throat land."},
    "cooling": {"count": 6, "width_rad": 0.14, "hot_ligament_m": 0.0015, "depth_m": 0.0025, "basis": "Six axial sector passages and closed fluid-domain bodies for CAD illustration. Not sized for heat flux; no manifolds, boiling model, thermal solve, film cooling or demonstrated coolability. Not silently coupled to rectangular thermal channels."},
    "injector": {"type": "doublet", "pairs": 8, "hole_radius_m": 0.001, "thickness_m": 0.008, "separation_m": 0.010, "angle_rad": 0.25, "basis": "Sixteen inclined bores in a provisional unassigned-port plate. No propellant routing, flow-area/Cd/pressure-drop sizing, atomization, stability or fuel/oxidizer manifolds. 1 mm exploded assembly gap is display intent, not a sealed joint."},
    "tolerances": "Source 1 um, tessellation 0.15 mm. Software-QA ceilings are declared before build, not manufacturing tolerances.",
    "pending": ["Feed/tank pressure and injector hydraulic sizing", "Material and burn-duration selection", "Cooling/thermal and structural assessment", "Combustion efficiency and stability", "Sealed joints, manifolds, valves, mounting and plumbing", "Independent qualified review", "Physical validation with measured uncertainty"],
}


def q(value, unit="m"):
    return {"value": value, "unit": unit}


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def study(destination):
    engine = bind_nasa_cea_engine(fuel_temperature_k=TF, oxidizer_temperature_k=TO,
                                 exit_pressure_pa=PA, require_explicit_temperatures=True)
    rows = []

    def evaluate(of, equilibrium, label):
        try:
            result = run_thermochemistry(CeaRequest("LCH4", "LOX", of, pascal(PC),
                                        equilibrium=equilibrium), engine=engine)
        except ThermochemistryError as exc:
            row = {"mixture_ratio": of, "mode": "equilibrium" if equilibrium else "chamber-frozen",
                   "grid": label, "status": "REJECTED", "error": str(exc),
                   **dict.fromkeys(("specific_impulse_s", "expansion_ratio", "cstar_m_s",
                      "chamber_temperature_k", "exit_pressure_pa", "exit_mach", "force_per_throat_area_n_m2"))}
            rows.append(row)
            return row, None
        exit_ = result.rocket_stations["exit"]
        scaled = scale_external_nozzle(pascal(PC), pascal(PA), square_metre(1.0),
            exit_["area_ratio"], result.characteristic_velocity,
            quantity(exit_["velocity_m_s"], SI.get("m/s")), pascal(exit_["pressure_pa"]))
        row = {"mixture_ratio": of, "mode": "equilibrium" if equilibrium else "chamber-frozen",
               "grid": label, "status": "CONVERGED", "error": "", "specific_impulse_s": scaled.specific_impulse_s,
               "expansion_ratio": exit_["area_ratio"], "cstar_m_s": result.characteristic_velocity.to_si(),
               "chamber_temperature_k": result.chamber_temperature.to_si(),
               "exit_pressure_pa": exit_["pressure_pa"], "exit_mach": exit_["mach"],
               "force_per_throat_area_n_m2": scaled.force.to_si()}
        rows.append(row)
        return row, result

    for equilibrium in (True, False):
        coarse = [evaluate(round(1.5 + i * 0.05, 6), equilibrium, "coarse")[0] for i in range(61)]
        valid = [r for r in coarse if r["status"] == "CONVERGED"]
        if not valid:
            if equilibrium:
                raise RuntimeError("No valid equilibrium study points; no baseline selection permitted.")
            continue  # Retain all rejected optional frozen cases; never substitute an assumed solution.
        best = max(valid, key=lambda row: row["specific_impulse_s"])
        if best is coarse[0] or best is coarse[-1]:
            raise RuntimeError("O/F optimum hit study boundary; expand documented study before selecting.")
        refined = [evaluate(round(best["mixture_ratio"] - 0.05 + i * 0.001, 6), equilibrium, "refined")[0] for i in range(101)]
        if any(r["status"] != "CONVERGED" for r in refined):
            raise RuntimeError("Selected neighborhood contains rejected CEA points; no automatic optimum claim.")
    selected = max((r for r in rows if r["mode"] == "equilibrium" and r["status"] == "CONVERGED"), key=lambda r: r["specific_impulse_s"])
    _, selected_thermo = evaluate(selected["mixture_ratio"], True, "selected-replay")
    # Sensitivity is evaluated at the SAME selected geometry, not just a separately optimized frozen nozzle.
    frozen = None
    frozen_error = None
    try:
        frozen = run_thermochemistry(CeaRequest("LCH4", "LOX", selected["mixture_ratio"], pascal(PC),
            equilibrium=False, expansion_ratio=selected["expansion_ratio"]), engine=engine)
    except ThermochemistryError as exc:
        frozen_error = str(exc)
    at = TARGET / selected["force_per_throat_area_n_m2"]
    selected = {**selected, "throat_area_m2": at, "throat_diameter_m": 2*math.sqrt(at/math.pi),
                "exit_diameter_m": 2*math.sqrt(at*selected["expansion_ratio"]/math.pi),
                "mass_flow_kg_s": PC*at/selected["cstar_m_s"]}
    selected["fuel_flow_kg_s"] = selected["mass_flow_kg_s"]/(1+selected["mixture_ratio"])
    selected["oxidizer_flow_kg_s"] = selected["mass_flow_kg_s"]-selected["fuel_flow_kg_s"]
    frozen_record = {"status": "UNAVAILABLE", "error": frozen_error,
        "basis": "Existing strict adapter rejects native non-finite station data. No fallback or frozen-performance claim."}
    if frozen is not None:
        fe = frozen.rocket_stations["exit"]
        frozen_scaled = scale_external_nozzle(pascal(PC), pascal(PA), square_metre(at),
            selected["expansion_ratio"], frozen.characteristic_velocity,
            quantity(fe["velocity_m_s"], SI.get("m/s")), pascal(fe["pressure_pa"]))
        frozen_record = {"status": "CONVERGED", "thrust_n": frozen_scaled.force.to_si(),
            "specific_impulse_s": frozen_scaled.specific_impulse_s, "exit_pressure_pa": fe["pressure_pa"],
            "rocket_stations": frozen.rocket_stations, "provenance": frozen.provenance}
    save_json(destination/"cea-study.json", {"assumptions": ASSUMPTIONS, "inputs": {
        "thrust_target_n": TARGET, "chamber_pressure_absolute_pa": PC, "ambient_pressure_pa": PA,
        "fuel": "LCH4", "oxidizer": "LOX", "fuel_temperature_k": TF, "oxidizer_temperature_k": TO,
        "cycle": "PRESSURE_FED", "physical_validation": "NOT_PERFORMED"},
        "selected": selected, "rows": rows, "selected_rocket_stations": selected_thermo.rocket_stations,
        "selected_cea_provenance": selected_thermo.provenance,
        "same_geometry_frozen_sensitivity": frozen_record,
        "sources": ["https://www.nasa.gov/glenn/research/chemical-equilibrium-with-applications/",
                    "https://github.com/nasa/cea/tree/v3.3.4", "https://ntrs.nasa.gov/citations/19710019929"]})
    with (destination/"cea-study.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    return selected


def baseline(selected):
    design = create_design(name="Methalox 1.5 kN · 5 bar abs · preliminary concept",
        description="User-authorized sea-level static ideal CEA study and provisional 3D thrust-chamber concept. NOT manufacturing, hot-fire or physical approval.")
    update_requirements(design, {"target_thrust": TARGET, "target_chamber_pressure": PC,
        "ambient_pressure": PA, "operating_altitude": 0.0,
        "mixture_ratio": selected["mixture_ratio"], "expansion_ratio": selected["expansion_ratio"],
        "notes": "No burn duration or material selected. " + json.dumps(ASSUMPTIONS)})
    update_propellants(design, fuel_id="LCH4", oxidizer_id="LOX", mixture_ratio=selected["mixture_ratio"])
    update_cycle(design, "PRESSURE_FED")
    configure_subsystems(design, {"nozzle": {key: value for key, value in ASSUMPTIONS["contour"].items() if key != "basis"}})
    result = run_phase3(design, throat_area_m2=selected["throat_area_m2"], expansion_ratio=selected["expansion_ratio"],
        thermochemistry_configuration={"mode": "nasa_cea", "fuel_temperature_k": TF, "oxidizer_temperature_k": TO})
    if not result["execution_ok"]:
        raise RuntimeError("Phase3 failed: " + json.dumps({k: v.get("errors") for k,v in result["stages"].items()}))
    chamber = run_chamber_stage(design, characteristic_length_m=0.8, contraction_ratio=3.0)
    nozzle = run_nozzle_stage(design, require_contour=True)
    for stage in (chamber, nozzle):
        if stage.status.value != "CURRENT":
            raise RuntimeError("Required geometric stage failed: " + json.dumps(stage.to_canonical_dict()))
    force = design.workflow.current_result("performance").outputs["thrust"]["magnitude"]
    if not math.isclose(force, TARGET, rel_tol=2e-4):
        raise RuntimeError(f"Selected study vs baseline sizing mismatch: {force} N")
    return design


def execute(destination):
    selected = study(destination)
    print(json.dumps({"study_selected": selected}), flush=True)
    design = baseline(selected)
    app = CosmosApplication(destination/"app-data", new_shell=True, durable_projects=True,
                            ngg_enabled=True, ngg_runtime=RUNTIME)
    try:
        api = app.project_api
        actor = principal(next(user for user in app.auth.list_users() if user.login_id == "cosmos-admin"))
        project = api.repository.create_project(actor, title="Methalox 1500 N / 5 bar abs — preliminary",
            mission="Sea-level static CEA ideal sizing and unreviewed native thrust-chamber concept", operation_id="methalox-concept-project")
        saved = api.service.create(actor, project.project_id, design=design, operation_id="baseline",
                                   command_hash=sha256(json.dumps(design.to_canonical_dict(), sort_keys=True).encode()).hexdigest())
        seeded = api.components.models.seed(actor, project.project_id, saved.commit_id, {
            "wall_thickness": q(.006), "convergent_length": q(.045), "throat_land_length": q(.003),
            "source_tolerance": q(1e-6), "export_tolerance": q(.00015),
            "source": "Actual selected CEA engine baseline and exact saved contour; user-authorized provisional concept dimensions in assumptions.json; no thermal/material/hardware acceptance."})
        spec = seeded["specification"]
        first = spec["features"][0]["parameters"]
        x0, radius = first["x0"]["value"], first["inner0"]["value"]
        spec["frames"].append({"id": "injector-frame", "parent": "world",
            "origin": [q(x0-.009), q(0.), q(0.)], "rotation": [1.,0.,0.,0.,1.,0.,0.,0.,1.]})
        spec["features"].extend([
            {"id": "cooling-passages", "operation": "cooling.axial_sector", "frame": "world",
             "depends_on": ["thrust-chamber"], "parameters": {"count": q(6,"1"), "width": q(.14,"rad"),
              "hot_ligament": q(.0015), "depth": q(.0025), "phase": q(.1,"rad"), "fluid_domains": q(1,"1")}},
            {"id": "injector-doublet", "operation": "injector.doublet", "frame": "injector-frame",
             "depends_on": [], "parameters": {"radius": q(radius+.006), "thickness": q(.008),
              "ring_radius": q(radius*.65), "count": q(8,"1"), "hole_radius": q(.001),
              "phase": q(0.,"rad"), "separation": q(.010), "angle": q(.25,"rad")}},
        ])
        spec["outputs"] = ["cooling-passages", "injector-doublet"]
        compile_model(spec, "engine-component-methalox-concept", "preliminary-v1", datetime.now(timezone.utc).isoformat())
        model = api.components.handle(actor, "POST", project.project_id, "component-geometry", [], {}, {
            "title": "Methalox thrust chamber + illustrative cooling + doublet plate — unreviewed",
            "baseline_commit_id": saved.commit_id, "expected_baseline": asdict(saved.head),
            "specification": spec, "expected": asdict(Head.absent()), "operation_id": "concept-components"})
        limits = {"relative_volume": q(.01,"1"), "centroid": q(.0003), "implicit_residual": q(.0003),
            "reverse_distance": q(.0003), "semantic_relative_area": q(.001,"1"), "semantic_centroid": q(1e-5),
            "source": "Predeclared concept SOFTWARE-QA: 1% volume, 0.30 mm mesh distances, 0.1% semantic area / 0.01 mm semantic centroid. Not manufacture or engineering acceptance."}
        job = api.components.builds.handle(actor, "POST", project.project_id, [], {}, {
            "model_commit_id": model["authority"]["commit_id"], "expected_model": model["authority"]["head"],
            "qa_specification": limits, "output_formats": ["step", "stl"], "operation_id": "native-concept-build"})
        identifiers = {"project_id": project.project_id, "design_id": saved.object_id,
            "baseline_commit_id": saved.commit_id, "model_id": model["authority"]["object_id"],
            "model_commit_id": model["authority"]["commit_id"], "build_object_id": job["object_id"], "job_id": job["job_id"]}
        save_json(destination/"identities.json", identifiers)
        save_json(destination/"assumptions.json", ASSUMPTIONS)
        save_json(destination/"component-specification.json", spec)
        (destination/"engine-baseline.json").write_bytes(saved.payload)
        deadline = time.monotonic()+360
        while job["state"] not in {"COMPLETED", "FAILED", "CANCELLED", "INTERRUPTED"}:
            if time.monotonic() > deadline:
                raise TimeoutError("Native build still pending; retained exact job is in identities.json")
            time.sleep(.5)
            job = api.components.builds.job(actor, api.components.jobs.get(actor, project.project_id, job["job_id"]))
        save_json(destination/"native-job.json", job)
        if job["state"] != "COMPLETED":
            raise RuntimeError("Native software QA failed; inspect native-job.json. No failed CAD delivered.")
        for name in ("source.brep", "export.step", "export.stl"):
            (destination/("PRELIMINARY-UNREVIEWED-"+name)).write_bytes(api.components.jobs.blob(actor, project.project_id, job["job_id"], name))
        save_json(destination/"software-qa.json", job["qa"])
        print(json.dumps({"native_state": job["state"], "current_candidate": job["current_generated_candidate"], **identifiers}), flush=True)
    finally:
        app.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="NEW output directory; existing paths are refused")
    args = parser.parse_args()
    destination = args.output.expanduser().absolute()
    destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    save_json(destination/"assumptions.json", ASSUMPTIONS)
    try:
        execute(destination)
    except Exception as exc:
        save_json(destination/"FAILED.json", {"type": type(exc).__name__, "error": str(exc), "cad_delivered": False})
        raise
    hashes = {p.name: sha256(p.read_bytes()).hexdigest() for p in destination.iterdir() if p.is_file()}
    save_json(destination/"artifact-sha256.json", hashes)


if __name__ == "__main__":
    main()
