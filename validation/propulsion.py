"""Predeclared propulsion comparison workflow, never automatic physical acceptance.

NIST TN1297 Appendix A, covariance propagation for a difference; section6,
expanded uncertainty k*u. No coverage probability is inferred from k alone.
https://www.nist.gov/pml/nist-technical-note-1297
"""

from __future__ import annotations

import csv
import io
import math
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
from typing import Any

PLAN_SCHEMA = "cosmos.propulsion-validation-plan.v1"
MEASUREMENT_SCHEMA = "cosmos.propulsion-measurement.v1"
CSV_HEADER = ["kind", "name", "value", "unit", "standard_uncertainty"]
MAX_CSV_BYTES = 1024 * 1024
PROVENANCE = {
    "kind",
    "source",
    "author",
    "version",
    "license",
    "instrumentation",
    "calibration_record",
    "uncertainty_basis",
    "acquired_at",
    "calibration_usage",
    "criteria_predefinition_basis",
}


def fields(value: Any, keys: set[str], name: str) -> None:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(
            f"{name} requires exactly {', '.join(sorted(keys))}; posted predictions/acceptance flags are not authority."
        )


def text(value: Any, name: str) -> str:
    if (
        type(value) is not str
        or not value.strip()
        or len(value) > 2048
        or "\0" in value
    ):
        raise ValueError(
            f"{name} needs bounded nonempty text/source, not a missing value."
        )
    return value


def number(value: Any, name: str, *, minimum: float | None = None) -> float:
    if type(value) not in {int, float}:
        raise ValueError(f"{name} must be a finite real number, not Boolean/text.")
    result = float(value)
    if (
        not math.isfinite(result)
        or abs(result) > 1e100
        or (minimum is not None and result < minimum)
    ):
        raise ValueError(f"{name} is outside the finite comparison domain.")
    return result


def unit_value(value: Any, unit: str, name: str, *, minimum: float = 0) -> float:
    fields(value, {"value", "unit"}, name)
    if value["unit"] != unit:
        raise ValueError(
            f"{name} requires explicit SI unit {unit}; no inferred conversion."
        )
    return number(value["value"], name, minimum=minimum)


def context_rows(candidate: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (kind, name): row
        for kind, field in (("condition", "conditions"), ("property", "properties"))
        for name, row in candidate[field].items()
    }


def plan(specification: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    fields(
        specification,
        {
            "schema",
            "intended_use",
            "applicability_basis",
            "targets",
            "context_tolerances",
        },
        "predeclared plan",
    )
    if specification["schema"] != PLAN_SCHEMA:
        raise ValueError("Unsupported propulsion validation plan schema.")
    text(specification["intended_use"], "intended use")
    text(specification["applicability_basis"], "model applicability/review basis")
    targets = specification["targets"]
    if (
        type(targets) is not dict
        or not 1 <= len(targets) <= 8
        or set(targets) != set(candidate["predictions"])
    ):
        raise ValueError(
            "Declare1-8 exactly supported target quantities; no client prediction values."
        )
    for name, criteria in targets.items():
        fields(
            criteria,
            {
                "max_absolute_error",
                "max_combined_standard_uncertainty",
                "prediction_standard_uncertainty",
                "prediction_uncertainty_basis",
                "coverage_factor",
                "correlation",
            },
            name + " criteria",
        )
        unit = candidate["predictions"][name]["unit"]
        for key in ("max_absolute_error", "max_combined_standard_uncertainty"):
            unit_value(criteria[key], unit, key)
        if criteria["prediction_standard_uncertainty"] is not None:
            unit_value(
                criteria["prediction_standard_uncertainty"],
                unit,
                "prediction uncertainty",
            )
        text(
            criteria["prediction_uncertainty_basis"],
            "prediction uncertainty basis; explicitly state unknown when unavailable",
        )
        coverage = number(criteria["coverage_factor"], "coverage factor", minimum=1)
        correlation = number(criteria["correlation"], "correlation", minimum=-1)
        if coverage > 10 or correlation > 1:
            raise ValueError(
                "Require1<=coverage_factor<=10 and -1<=correlation<=1; no confidence probability inferred."
            )
    tolerances = specification["context_tolerances"]
    expected = {
        kind + "." + name: row
        for (kind, name), row in context_rows(candidate).items()
        if type(row["value"]) in {int, float}
    }
    fields(tolerances, set(expected), "numeric context/property tolerances")
    for key, row in expected.items():
        unit_value(tolerances[key], row["unit"], key)
    return {
        "schema": PLAN_SCHEMA,
        "specification": deepcopy(specification),
        "candidate": deepcopy(candidate),
        "physical_validation": "NOT_PERFORMED",
        "readiness": "AWAITING_MEASUREMENTS",
        "blockers": [
            "MEASUREMENT_DATA_MISSING",
            "MODEL_APPLICABILITY_REVIEW_REQUIRED",
            "COMPLETE_UNCERTAINTY_BUDGET_REVIEW_REQUIRED",
            "INDEPENDENT_QUALIFIED_ACCEPTANCE_REQUIRED",
        ],
    }


def template(value: dict[str, Any]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(CSV_HEADER)
    for (kind, name), row in context_rows(value["candidate"]).items():
        writer.writerow([kind, name, "", row["unit"], ""])
    for name, row in value["candidate"]["predictions"].items():
        writer.writerow(["target", name, "", row["unit"], ""])
    return output.getvalue().encode()


def measurement(
    raw: bytes, metadata: dict[str, Any], original_plan: dict[str, Any]
) -> dict[str, Any]:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_CSV_BYTES:
        raise ValueError(
            "Measurement CSV requires1 byte to1MiB of exact UTF-8 originals."
        )
    fields(metadata, PROVENANCE, "measurement provenance")
    for key in PROVENANCE:
        text(metadata[key], key)
    if metadata["kind"] not in {
        "experimental",
        "published-experimental",
        "synthetic",
    } or metadata["calibration_usage"] not in {
        "held-out",
        "calibration",
        "not-applicable",
    }:
        raise ValueError(
            "Explicit experimental/published-experimental/synthetic kind and held-out/calibration/not-applicable usage required."
        )
    timestamp = datetime.fromisoformat(metadata["acquired_at"].replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("Acquisition timestamp needs an explicit UTC offset.")
    expected = {
        **context_rows(original_plan["candidate"]),
        **{
            ("target", name): row
            for name, row in original_plan["candidate"]["predictions"].items()
        },
    }
    reader = csv.DictReader(
        io.StringIO(raw.decode("utf-8", errors="strict"), newline="")
    )
    if reader.fieldnames != CSV_HEADER:
        raise ValueError("CSV header/order must match the exact emitted template.")
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for index, row in enumerate(reader):
        if index >= 128 or None in row or any(v is None for v in row.values()):
            raise ValueError(
                "At most128 complete CSV rows; extra/missing columns refused."
            )
        row_key = (row["kind"], row["name"])
        if row_key not in expected or row_key in seen:
            raise ValueError("Unknown or duplicate measurement/context/property row.")
        original = expected[row_key]
        if row["unit"] != original["unit"]:
            raise ValueError(
                "Measurement SI units must exactly match the plan; no conversion or inferred alignment."
            )
        if not row["value"].strip():
            raise ValueError(
                "Empty measurement templates are not evidence; no values or uncertainty are defaulted."
            )
        if type(original["value"]) is str:
            value: float | str = text(row["value"], "measured identity")
            if row["standard_uncertainty"] != "":
                raise ValueError(
                    "Identity rows have no numerical standard uncertainty."
                )
            uncertainty = None
        else:
            value = number(float(row["value"]), "measured value")
            if (
                row["unit"] in {"K", "kg/m3", "kg/mol", "J/kg/K", "Pa*s", "W/m/K", "m2"}
                and value <= 0
            ):
                raise ValueError(
                    "Absolute temperature and declared positive material/geometric properties must be positive."
                )
            uncertainty = number(
                float(row["standard_uncertainty"]),
                "measurement standard uncertainty",
                minimum=0,
            )
            if uncertainty == 0:
                raise ValueError(
                    "Every numeric observation/property/condition needs positive reported standard uncertainty."
                )
        seen[row_key] = {
            "value": value,
            "unit": row["unit"],
            "standard_uncertainty": uncertainty,
        }
    if set(seen) != set(expected):
        raise ValueError(
            "All predeclared target, condition and property rows are required; no omission/substitution."
        )
    return {
        "schema": MEASUREMENT_SCHEMA,
        "provenance": deepcopy(metadata),
        "source_sha256": sha256(raw).hexdigest(),
        "rows": [
            {"kind": key[0], "name": key[1], **value} for key, value in seen.items()
        ],
        "authenticity": "ASSERTED_SOURCE_PENDING_INDEPENDENT_REVIEW",
        "physical_validation": "NOT_PERFORMED",
    }


def compare(
    original_plan: dict[str, Any], measurements: dict[str, Any]
) -> dict[str, Any]:
    supplied = {(row["kind"], row["name"]): row for row in measurements["rows"]}
    context = []
    for (kind, name), expected in context_rows(original_plan["candidate"]).items():
        actual = supplied[(kind, name)]
        if type(expected["value"]) is str:
            passed = actual["value"] == expected["value"]
            difference, tolerance = None, None
        else:
            difference = actual["value"] - expected["value"]
            tolerance = original_plan["specification"]["context_tolerances"][
                kind + "." + name
            ]["value"]
            passed = abs(difference) <= tolerance
        context.append(
            {
                "kind": kind,
                "name": name,
                "unit": expected["unit"],
                "expected": expected["value"],
                "observed": actual["value"],
                "signed_difference": difference,
                "tolerance": tolerance,
                "passed": passed,
            }
        )
    context_pass = all(row["passed"] for row in context)
    targets = []
    for name, prediction in original_plan["candidate"]["predictions"].items():
        actual = supplied[("target", name)]
        criteria = original_plan["specification"]["targets"][name]
        error = prediction["value"] - actual["value"]
        u = criteria["prediction_standard_uncertainty"]
        combined = (
            None
            if u is None
            else math.hypot(
                u["value"] - actual["standard_uncertainty"],
                math.sqrt(2 * (1 - criteria["correlation"]))
                * math.sqrt(u["value"])
                * math.sqrt(actual["standard_uncertainty"]),
            )
        )
        within_coverage = (
            None
            if combined is None
            else abs(error) <= criteria["coverage_factor"] * combined
        )
        uncertainty_pass = (
            None
            if combined is None
            else combined <= criteria["max_combined_standard_uncertainty"]["value"]
        )
        discrepancy_pass = abs(error) <= criteria["max_absolute_error"]["value"]
        targets.append(
            {
                "name": name,
                "unit": prediction["unit"],
                "prediction": prediction["value"],
                "measurement": actual["value"],
                "signed_error": error,
                "measurement_standard_uncertainty": actual["standard_uncertainty"],
                "combined_standard_uncertainty": combined,
                "discrepancy_passed": discrepancy_pass,
                "uncertainty_passed": uncertainty_pass,
                "within_declared_coverage": within_coverage,
                "eligible_software_comparison": context_pass
                and discrepancy_pass
                and uncertainty_pass is True
                and within_coverage is True,
            }
        )
    provenance = measurements["provenance"]
    blockers = [
        "SOURCE_AUTHENTICITY_REVIEW_REQUIRED",
        "MODEL_APPLICABILITY_REVIEW_REQUIRED",
        "COMPLETE_UNCERTAINTY_BUDGET_REVIEW_REQUIRED",
        "INDEPENDENT_QUALIFIED_ACCEPTANCE_REQUIRED",
    ]
    if not context_pass:
        blockers.append("OPERATING_CONDITION_OR_PROPERTY_MISMATCH")
    if provenance["kind"] == "synthetic":
        blockers.append("SYNTHETIC_IS_NOT_PHYSICAL_EVIDENCE")
    if provenance["calibration_usage"] != "held-out":
        blockers.append("NOT_INDEPENDENT_HELD_OUT_EVIDENCE")
    if any(row["combined_standard_uncertainty"] is None for row in targets):
        blockers.append("PREDICTION_UNCERTAINTY_UNKNOWN")
    if not all(row["eligible_software_comparison"] for row in targets):
        blockers.append("DECLARED_SOFTWARE_COMPARISON_NOT_PASSED")
    return {
        "schema": "cosmos.propulsion-validation-assessment.v1",
        "execution": "COMPLETED",
        "context": context,
        "targets": targets,
        "software_comparison_passed": all(
            row["eligible_software_comparison"] for row in targets
        ),
        "physical_validation": "NOT_PERFORMED",
        "independent_acceptance": False,
        "production_handoff": False,
        "readiness": "EVIDENCE_PENDING_QUALIFIED_REVIEW"
        if provenance["kind"] != "synthetic"
        and provenance["calibration_usage"] == "held-out"
        else "NOT_PHYSICAL_VALIDATION",
        "blockers": blockers,
        "uncertainty_scope": "Correlated reported output uncertainties only; no complete input/model/numerical uncertainty budget or coverage probability inferred. Context/property uncertainties are retained, not silently propagated into model outputs.",
    }
