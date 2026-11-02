"""Temperature discrepancy and conditional output-uncertainty assessment in SI."""
from __future__ import annotations

import math
from typing import Any

from systems.contracts.geometry._wire import require

from .contracts import Criteria, ThermalDataset


def compare(candidate: ThermalDataset, reference: ThermalDataset, criteria: Criteria) -> dict[str, Any]:
    a, b, p = candidate.data, reference.data, criteria.data
    require(a["kind"] in {"simulation", "external-solver"} and b["kind"] != "simulation", "INVALID_COMPARISON", "A simulation/external solver must be compared with independent reference evidence")
    require(a["provenance"]["source_sha256"] != b["provenance"]["source_sha256"], "SELF_COMPARISON", "Identical source bytes are not independent evidence")
    require(a["model_id"] == b["model_id"] and a["frame_id"] == b["frame_id"], "FRAME_MODEL_MISMATCH", "Coordinate frame and model must match; no inferred transform")
    require(a["conditions"] == b["conditions"], "CONDITION_MISMATCH", "Geometry, material property and boundary conditions must match exactly in SI")
    needs_conversion = any(d["coordinate_unit"] != "m" or d["value_unit"] != "K" for d in (a, b))
    require(not needs_conversion or p["allow_unit_conversion"], "UNIT_CONVERSION_REQUIRED", "Declare explicit conversion before importing the reference")
    def coordinates(d: dict[str, Any]) -> list[float]:
        return [v * (0.001 if d["coordinate_unit"] == "mm" else 1) for v in d["coordinates"]]
    x, other = coordinates(a), coordinates(b)
    require(len(x) == len(other) and all(math.isclose(v, w, rel_tol=1e-12, abs_tol=1e-15) for v, w in zip(x, other)),
            "ALIGNMENT_REQUIRED", "Observation radii must match; no extrapolation, hidden interpolation or resampling")
    av = [v + (273.15 if a["value_unit"] == "degC" else 0) for v in a["values"]]
    bv = [v + (273.15 if b["value_unit"] == "degC" else 0) for v in b["values"]]
    errors = [v - w for v, w in zip(av, bv)]
    au, bu = a["standard_uncertainty_k"], b["standard_uncertainty_k"]
    combined = [math.sqrt(max(0, v*v + w*w - 2*p["correlation"]*v*w)) for v, w in zip(au, bu)] if au is not None and bu is not None else None
    error_pass = max(abs(v) for v in errors) <= p["max_abs_error_k"]
    uncertainty_pass = max(combined) <= p["max_combined_standard_uncertainty_k"] if combined is not None else None
    discrepancy_coverage = [abs(e) <= p["coverage_factor"]*u for e, u in zip(errors, combined)] if combined is not None else None
    measured = b["kind"] == "experimental"
    held_out = b["provenance"]["calibration_usage"] == "held-out"
    return {"schema_version": "p10-assessment-v1", "kind": "thermal", "candidate_sha256": candidate.content_sha256,
            "reference_sha256": reference.content_sha256, "criteria_sha256": criteria.content_sha256,
            "execution": "completed", "coordinate_unit": "m", "value_unit": "K", "coordinates_m": x,
            "candidate_k": av, "reference_k": bv, "signed_error_k": errors,
            "metrics": {"bias_k": math.fsum(errors)/len(errors), "rmse_k": math.sqrt(math.fsum(v*v for v in errors)/len(errors)),
                        "max_abs_error_k": max(abs(v) for v in errors), "sample_count": len(errors)},
            "alignment": "matching coordinates; roundoff-only 1e-12 relative/1e-15m absolute; no interpolation",
            "unit_conversion": "explicit-mm/degC-to-SI" if needs_conversion else "none",
            "combined_standard_uncertainty_k": combined, "coverage_factor": p["coverage_factor"], "correlation": p["correlation"],
            "uncertainty_scope": "Reported output standard uncertainties only; missing input/model/numerical contributions are not inferred. No normality or coverage probability is asserted.",
            "error_criteria_passed": error_pass, "uncertainty_criteria_passed": uncertainty_pass,
            "discrepancy_within_declared_coverage": discrepancy_coverage,
            "reference_kind": b["kind"], "calibration_usage": b["provenance"]["calibration_usage"],
            "experimental_validation": "evidence-pending-independent-review" if measured and held_out else "calibration-only-not-validation" if measured else "not-performed",
            "software_comparison": "within-declared-discrepancy-limit" if error_pass else "outside-declared-discrepancy-limit",
            "engineering_review": "pending", "independent_acceptance": False, "production_handoff": False,
            "provenance_authenticity": "Imported source assertions require independent review; a checksum is not authentication",
            "blockers": (["EXPERIMENTAL_SOURCE_AND_SCOPE_REVIEW_REQUIRED"] if measured else ["NO_MEASURED_REFERENCE"])
                        + (["CALIBRATION_DATA_NOT_HELD_OUT"] if measured and not held_out else [])
                        + (["OUTPUT_UNCERTAINTY_INCOMPLETE"] if combined is None else [])
                        + ["FULL_UNCERTAINTY_BUDGET_REVIEW_REQUIRED", "INDEPENDENT_ENGINEERING_ACCEPTANCE_REQUIRED"]}
