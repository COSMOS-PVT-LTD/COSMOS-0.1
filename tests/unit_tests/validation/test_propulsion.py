"""Independent uncertainty/context parser fixtures; no genuine experimental data."""

from copy import deepcopy

import pytest

from tests.fixtures.propulsion_validation import csv_data, metadata, specification
from validation import propulsion as vv


def basis():
    return {
        "predictions": {"thrust": {"value": 100.0, "unit": "N"}},
        "conditions": {
            "pressure": {"value": 200.0, "unit": "Pa"},
            "fuel_id": {"value": "synthetic-fuel", "unit": "1"},
        },
        "properties": {"density": {"value": 800.0, "unit": "kg/m3"}},
    }


def prepared(**edits):
    value = basis()
    return vv.plan(specification(value, **edits), value)


def test_blank_template_cannot_become_measurement_or_physical_evidence():
    plan = prepared()
    assert plan["readiness"] == "AWAITING_MEASUREMENTS"
    raw = vv.template(plan)
    assert b"100.0" not in raw and b"800.0" not in raw
    with pytest.raises(ValueError, match="Empty"):
        vv.measurement(raw, metadata(), plan)


def test_independent_three_four_five_uncertainty_and_nonacceptance():
    plan = prepared()
    data = vv.measurement(csv_data(plan, discrepancy=5), metadata(), plan)
    result = vv.compare(plan, data)
    row = result["targets"][0]
    assert row["signed_error"] == 5 and row[
        "combined_standard_uncertainty"
    ] == pytest.approx(5, rel=1e-14)
    assert result["software_comparison_passed"]
    assert (
        result["physical_validation"] == "NOT_PERFORMED"
        and not result["independent_acceptance"]
    )
    assert "SYNTHETIC_IS_NOT_PHYSICAL_EVIDENCE" in result["blockers"]


@pytest.mark.parametrize("correlation,expected", [(1, 1), (-1, 7), (0, 5)])
def test_covariance_sign_independent_constants(correlation, expected):
    b = basis()
    spec = specification(b)
    spec["targets"]["thrust"]["correlation"] = correlation
    plan = vv.plan(spec, b)
    result = vv.compare(plan, vv.measurement(csv_data(plan), metadata(), plan))
    assert result["targets"][0]["combined_standard_uncertainty"] == pytest.approx(
        expected
    )


@pytest.mark.parametrize(
    "kind,name",
    [("condition", "pressure"), ("property", "density"), ("condition", "fuel_id")],
)
def test_condition_or_material_property_mismatch_blocks_even_identical_outputs(
    kind, name
):
    plan = prepared()
    data = vv.measurement(csv_data(plan), metadata(), plan)
    row = next(
        row for row in data["rows"] if row["kind"] == kind and row["name"] == name
    )
    row["value"] = "wrong fuel" if type(row["value"]) is str else row["value"] + 1
    result = vv.compare(plan, data)
    assert not result["software_comparison_passed"]
    assert "OPERATING_CONDITION_OR_PROPERTY_MISMATCH" in result["blockers"]


def test_unknown_prediction_uncertainty_not_filled_with_zero():
    plan = prepared(unknown=True)
    result = vv.compare(plan, vv.measurement(csv_data(plan), metadata(), plan))
    assert result["targets"][0]["combined_standard_uncertainty"] is None
    assert not result["software_comparison_passed"]
    assert "PREDICTION_UNCERTAINTY_UNKNOWN" in result["blockers"]


@pytest.mark.parametrize(
    "change",
    [
        "duplicate",
        "missing",
        "units",
        "nonfinite",
        "zero_uncertainty",
        "header",
        "unknown",
    ],
)
def test_invalid_raw_csv_refused(change):
    plan = prepared()
    raw = csv_data(plan)
    lines = raw.decode().splitlines()
    if change == "duplicate":
        raw += (lines[-1] + "\r\n").encode()
    elif change == "missing":
        raw = ("\n".join(lines[:-1]) + "\n").encode()
    elif change == "units":
        raw = raw.replace(b",N,", b",kN,")
    elif change == "nonfinite":
        raw = raw.replace(b",100.0,N,", b",NaN,N,")
    elif change == "zero_uncertainty":
        raw = raw.replace(b",N,4", b",N,0")
    elif change == "header":
        raw = raw.replace(b"standard_uncertainty", b"posted_acceptance")
    else:
        raw = raw.replace(b"target,thrust", b"target,posted_success")
    with pytest.raises(ValueError):
        vv.measurement(raw, metadata(), plan)


def test_claiming_experimental_heldout_is_not_authentication_or_acceptance():
    plan = prepared()
    # Deliberately asserted metadata tests the software gate; data remains synthetic.
    data = vv.measurement(
        csv_data(plan),
        metadata(kind="experimental", calibration_usage="held-out"),
        plan,
    )
    result = vv.compare(plan, data)
    assert result["software_comparison_passed"] and not result["independent_acceptance"]
    assert result["physical_validation"] == "NOT_PERFORMED"
    assert "SOURCE_AUTHENTICITY_REVIEW_REQUIRED" in result["blockers"]


@pytest.mark.parametrize("bad", [True, float("nan"), -1, "0"])
def test_plan_rejects_invalid_or_coerced_tolerance(bad):
    b = basis()
    spec = specification(b)
    spec["targets"]["thrust"]["max_absolute_error"]["value"] = bad
    with pytest.raises(ValueError):
        vv.plan(spec, b)


def test_no_posted_success_and_inputs_are_detached():
    b = basis()
    spec = specification(b)
    with pytest.raises(ValueError):
        vv.plan({**spec, "physical_validation": "PASSED"}, b)
    saved = vv.plan(spec, b)
    copy = deepcopy(saved)
    spec["targets"]["thrust"]["correlation"] = 0.5
    assert saved == copy
