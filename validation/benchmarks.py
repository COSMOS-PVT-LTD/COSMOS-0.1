"""Independent integration of the spherical equation, not a solver import."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .contracts import MODEL, ThermalDataset


def analytic(candidate: ThermalDataset) -> ThermalDataset:
    d = candidate.data
    c = d["conditions"]
    # Integrate r²T'=-qr³/(3k), then impose T(R)=Ts. No production
    # reference_temperature() or computed reference_k values are used here.
    x = [v * (0.001 if d["coordinate_unit"] == "mm" else 1) for v in d["coordinates"]]
    values = [c["surface_k"] + c["generation_w_m3"]/(6*c["conductivity_w_m_k"])*(c["radius_m"]**2-r*r) for r in x]
    return ThermalDataset.parse({"schema_version": "p10-thermal-v1", "kind": "analytic-reference", "quantity": "Temperature",
        "coordinate_unit": "m", "value_unit": "K", "frame_id": d["frame_id"], "model_id": MODEL,
        "conditions": c, "coordinates": x, "values": values, "standard_uncertainty_k": None,
        "provenance": {"source": "validation/benchmarks.py", "author": "COSMOS independent analytic verification fixture",
            "version": "p10-integrated-equation-v1", "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "license": "repository license", "method": "Independent integrated steady spherical equation; constants declared synthetic, not measured",
            "calibration_usage": "not-applicable", "uncertainty_basis": "Not statistical; analytic roundoff separate from discretization",
            "instrumentation": "not-applicable"}})


def from_run(run: dict[str, Any]) -> ThermalDataset:
    from systems.contracts.geometry._wire import digest, require
    require(run["schema_version"] == "p09-dataset-v1" and run["execution_status"] == "completed"
            and run["numerical_convergence"] == "converged" and run["conservation_checks"]["passed"]
            and run["solution_verification"] == "analytic-benchmark-passed", "UNVERIFIED_RUN", "Only complete, converged and verified P09 runs qualify")
    s, h = run["study"]["settings"], run["study"]["handoff"]
    return ThermalDataset.parse({"schema_version": "p10-thermal-v1", "kind": "simulation", "quantity": "Temperature",
        "coordinate_unit": "m", "value_unit": "K", "frame_id": h["frame_id"], "model_id": MODEL,
        "conditions": {"radius_m": h["radius_m"], **{key: s[key] for key in ("conductivity_w_m_k", "generation_w_m3", "surface_k")}},
        "coordinates": run["radii_m"], "values": run["temperature_k"], "standard_uncertainty_k": None,
        "provenance": {"source": "simulation/workbench.py", "author": "COSMOS local software benchmark", "version": run["study_id"],
            "source_sha256": digest(run), "license": "repository license", "method": "1D spherical finite volume; source dataset retained by exact run/study checksum",
            "calibration_usage": "not-applicable", "uncertainty_basis": "unknown", "instrumentation": "not-applicable"}})
