"""Synthetic evidence-parser/comparison fixtures ONLY, never hardware evidence."""

import csv
import io

from validation import propulsion as vv


def specification(basis, *, unknown=False):
    def q(value, unit):
        return {"value": value, "unit": unit}

    return {
        "schema": vv.PLAN_SCHEMA,
        "intended_use": "Synthetic software comparison/parser qualification only",
        "applicability_basis": "Synthetic test fixture; not engine or physical acceptance",
        "targets": {
            name: {
                "max_absolute_error": q(10, row["unit"]),
                "max_combined_standard_uncertainty": q(10, row["unit"]),
                "prediction_standard_uncertainty": None
                if unknown
                else q(3, row["unit"]),
                "prediction_uncertainty_basis": "Synthetic standard uncertainty for independent3-4-5 covariance fixture only",
                "coverage_factor": 2,
                "correlation": 0,
            }
            for name, row in basis["predictions"].items()
        },
        "context_tolerances": {
            kind + "." + name: q(0, row["unit"])
            for (kind, name), row in vv.context_rows(basis).items()
            if type(row["value"]) in {int, float}
        },
    }


def csv_data(plan, *, discrepancy=0):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(vv.CSV_HEADER)
    for (kind, name), row in vv.context_rows(plan["candidate"]).items():
        writer.writerow(
            [
                kind,
                name,
                row["value"],
                row["unit"],
                "" if type(row["value"]) is str else 1,
            ]
        )
    for name, row in plan["candidate"]["predictions"].items():
        writer.writerow(["target", name, row["value"] - discrepancy, row["unit"], 4])
    return output.getvalue().encode()


def metadata(**edits):
    return {
        "kind": "synthetic",
        "source": "synthetic://software-parser-fixture",
        "author": "Software regression fixture, not a measurement author",
        "version": "1",
        "license": "test fixture",
        "instrumentation": "Synthetic parser inputs, not an instrument",
        "calibration_record": "Synthetic fixture, no real calibration",
        "uncertainty_basis": "Synthetic standard uncertainties3 and4 for independently known5",
        "acquired_at": "2026-10-20T00:00:00+00:00",
        "calibration_usage": "not-applicable",
        "criteria_predefinition_basis": "Synthetic predeclared software test constants only",
        **edits,
    }
