"""Synthetic contract fixtures ONLY; these are not experimental evidence."""
from validation.contracts import MODEL


def dataset(kind="external-solver", source="1", uncertainty=None):
    return {"schema_version": "p10-thermal-v1", "kind": kind, "quantity": "Temperature", "coordinate_unit": "m", "value_unit": "K",
        "frame_id": "world", "model_id": MODEL, "conditions": {"radius_m": .01, "conductivity_w_m_k": 10., "generation_w_m3": 1e6, "surface_k": 300.},
        "coordinates": [.002, .004, .006, .008], "values": [301.6, 301.4, 301.1, 300.6], "standard_uncertainty_k": uncertainty,
        "provenance": {"source": "tests/fixtures/vv_cases.py", "author": "Synthetic contract test; no real experiment", "version": "test-v1",
            "source_sha256": source*64, "license": "repository license", "method": "Synthetic test observations; do not use for engineering validation",
            "calibration_usage": "held-out" if kind == "experimental" else "not-applicable",
            "uncertainty_basis": "Synthetic standard output uncertainty for unit tests only" if uncertainty else "unknown",
            "instrumentation": "Synthetic instrumentation metadata, no instrument exists" if kind == "experimental" else "not-applicable"}}


def criteria(convert=False):
    return {"intended_use": "Synthetic contract test only", "rationale": "Exercise comparison logic; not a physical acceptance basis",
            "max_abs_error_k": .5, "max_combined_standard_uncertainty_k": .5, "coverage_factor": 2., "correlation": 0., "allow_unit_conversion": convert}
