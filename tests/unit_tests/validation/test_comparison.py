"""Independent metrics and negative contracts; no synthetic physical validation."""
import copy
import hashlib
import json
import math

import pytest

from systems.contracts.geometry._wire import GeometryContractError
from tests.fixtures.vv_cases import criteria, dataset
from validation.benchmarks import analytic
from validation.comparison import compare
from validation.contracts import Criteria, ThermalDataset
from validation.workbench import ComparisonWorkbench


def test_signed_metrics_independent_hand_calculation_and_unknown_uncertainty():
    a, b = dataset(), dataset("analytic-reference", "2")
    a["values"] = [302.6, 303.4, 300.1, 300.6]
    result = compare(ThermalDataset.parse(a), ThermalDataset.parse(b), Criteria.parse(criteria()))
    assert result["signed_error_k"] == [1., 2., -1., 0.]
    assert result["metrics"]["bias_k"] == .5
    assert result["metrics"]["rmse_k"] == math.sqrt(1.5)
    assert result["metrics"]["max_abs_error_k"] == 2.
    assert result["error_criteria_passed"] is False
    assert result["combined_standard_uncertainty_k"] is None and result["uncertainty_criteria_passed"] is None
    assert result["experimental_validation"] == "not-performed" and result["production_handoff"] is False


@pytest.mark.parametrize("rho,expected", [(0., .5), (1., .1), (-1., .7)])
def test_declared_correlation_output_uncertainty_not_automatic_validation(rho, expected):
    p = criteria(); p["correlation"] = rho
    result = compare(ThermalDataset.parse(dataset(uncertainty=[.3]*4)), ThermalDataset.parse(dataset("experimental", "2", [.4]*4)), Criteria.parse(p))
    assert result["combined_standard_uncertainty_k"] == pytest.approx([expected]*4)
    assert result["experimental_validation"] == "evidence-pending-independent-review"
    assert result["independent_acceptance"] is False
    assert "FULL_UNCERTAINTY_BUDGET_REVIEW_REQUIRED" in result["blockers"]


def test_calibration_is_not_validation_even_with_zero_discrepancy():
    ref = dataset("experimental", "2", [.1]*4); ref["provenance"]["calibration_usage"] = "calibration"
    r = compare(ThermalDataset.parse(dataset(uncertainty=[.1]*4)), ThermalDataset.parse(ref), Criteria.parse(criteria()))
    assert r["experimental_validation"] == "calibration-only-not-validation" and r["error_criteria_passed"]


def test_large_uncertainty_cannot_pass_just_because_intervals_overlap():
    r = compare(ThermalDataset.parse(dataset(uncertainty=[10.]*4)), ThermalDataset.parse(dataset("experimental", "2", [10.]*4)), Criteria.parse(criteria()))
    assert all(r["discrepancy_within_declared_coverage"]) and r["uncertainty_criteria_passed"] is False


def test_explicit_boundary_conversion_and_roundoff_only_coordinate_alignment():
    ref = dataset("analytic-reference", "2"); ref["coordinate_unit"] = "mm"; ref["value_unit"] = "degC"
    ref["coordinates"] = [2., 4., 6., 8.]; ref["values"] = [v-273.15 for v in ref["values"]]
    with pytest.raises(GeometryContractError, match="Declare explicit"):
        compare(ThermalDataset.parse(dataset()), ThermalDataset.parse(ref), Criteria.parse(criteria()))
    r = compare(ThermalDataset.parse(dataset()), ThermalDataset.parse(ref), Criteria.parse(criteria(True)))
    assert r["metrics"]["max_abs_error_k"] < 1e-12 and r["unit_conversion"] == "explicit-mm/degC-to-SI"


@pytest.mark.parametrize("change,code", [("frame", "FRAME_MODEL_MISMATCH"), ("condition", "CONDITION_MISMATCH"), ("coordinates", "ALIGNMENT_REQUIRED"), ("same-source", "SELF_COMPARISON")])
def test_incompatible_or_self_comparison_refused(change, code):
    ref = dataset("analytic-reference", "2")
    if change == "frame": ref["frame_id"] = "other"
    if change == "condition": ref["conditions"]["surface_k"] = 301.
    if change == "coordinates": ref["coordinates"][0] = .001
    if change == "same-source": ref["provenance"]["source_sha256"] = "1"*64
    with pytest.raises(GeometryContractError) as caught:
        compare(ThermalDataset.parse(dataset()), ThermalDataset.parse(ref), Criteria.parse(criteria()))
    assert caught.value.code == code


@pytest.mark.parametrize("field,value", [("values", [math.nan]*4), ("values", [True]*4), ("values", [-1.]*4), ("coordinates", [.002]*4), ("standard_uncertainty_k", [-1.]*4), ("standard_uncertainty_k", [.1]), ("value_unit", "F"), ("quantity", "Pressure"), ("values", [300.]), ("model_id", "engine-cfd")])
def test_invalid_import_contract(field, value):
    d = dataset(); d[field] = value
    with pytest.raises(GeometryContractError): ThermalDataset.parse(d)


@pytest.mark.parametrize("field,value", [("max_abs_error_k", 0), ("coverage_factor", 0), ("correlation", 1.1), ("allow_unit_conversion", 1), ("max_combined_standard_uncertainty_k", math.inf)])
def test_invalid_criteria(field, value):
    p = criteria(); p[field] = value
    with pytest.raises(GeometryContractError): Criteria.parse(p)


@pytest.mark.parametrize("missing", ["uncertainty", "instrumentation", "basis"])
def test_experimental_metadata_requires_uncertainty_and_instruments(missing):
    d = dataset("experimental", "2", [.1]*4)
    if missing == "uncertainty": d["standard_uncertainty_k"] = None
    if missing == "instrumentation": d["provenance"]["instrumentation"] = "not-applicable"
    if missing == "basis": d["provenance"]["uncertainty_basis"] = "unknown"
    with pytest.raises(GeometryContractError) as caught: ThermalDataset.parse(d)
    assert caught.value.code == "EXPERIMENTAL_EVIDENCE_INCOMPLETE"


def test_immutable_defensive_copies_and_independent_formula():
    source = dataset(); d = ThermalDataset.parse(source); old = d.content_sha256
    source["values"][0] = 10.; d.data["values"][0] = 20.
    assert d.content_sha256 == old
    ref = analytic(d)
    assert ref.data["values"] == pytest.approx([301.6, 301.4, 301.0666666667, 300.6])
    assert ref.data["kind"] == "analytic-reference" and ref.data["standard_uncertainty_k"] is None


def test_predeclared_receipt_ownership_review_and_immutability(tmp_path):
    with_workbench = ComparisonWorkbench(tmp_path)
    try:
        w = with_workbench; a = w.imported("a", dataset())["dataset_id"]; p = w.declare("a", criteria())["criteria_id"]
        b = w.imported("a", dataset("analytic-reference", "2"))["dataset_id"]
        result = w.assess("a", a, b, p); before = copy.deepcopy(result)
        result["report"]["production_handoff"] = True
        assert w.report("a", before["report_id"])["report"] == before["report"]
        intent = w.review("a", before["report_id"], "Synthetic unit-test evidence inspection only")
        assert intent["independent_acceptance"] is False and intent["experimental_validation"] is False
        with pytest.raises(GeometryContractError): w.report("b", before["report_id"])
    finally:
        with_workbench.close()


def test_posthoc_reimport_cannot_hide_reference_exposure(tmp_path):
    w = ComparisonWorkbench(tmp_path)
    try:
        a = w.imported("a", dataset())["dataset_id"]; b = w.imported("a", dataset("analytic-reference", "2"))["dataset_id"]
        p = w.declare("a", criteria())["criteria_id"]; w.imported("a", dataset("analytic-reference", "2"))
        with pytest.raises(GeometryContractError) as caught: w.assess("a", a, b, p)
        assert caught.value.code == "POST_HOC_CRITERIA" and not w.context("a")["report_ids"]
    finally:
        w.close()


def test_receipt_exports_preserve_exact_canonical_bytes_across_numeric_formatting(tmp_path):
    w = ComparisonWorkbench(tmp_path)
    try:
        a = w.imported("a", dataset())["dataset_id"]
        p = w.declare("a", criteria())["criteria_id"]
        b = w.imported("a", dataset("analytic-reference", "2"))["dataset_id"]
        receipt = w.assess("a", a, b, p)
        raw = receipt["canonical_json"]
        assert hashlib.sha256(raw.encode()).hexdigest() == receipt["report_id"]
        assert json.loads(raw) == receipt["report"]
        assert '0.0' in raw
        # A JavaScript JSON round trip may spell 0.0 as 0 in display fields.
        exported = json.loads(json.dumps(receipt))
        exported["report"]["metrics"]["bias_k"] = 0
        assert exported["canonical_json"] == raw
        assert w.report("a", receipt["report_id"])["canonical_json"] == raw
    finally:
        w.close()
