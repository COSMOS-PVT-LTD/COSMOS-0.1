"""Visualization consumes finite detached outputs, never computes engine physics."""
import hashlib
import json
from copy import deepcopy

import pytest

from api.propulsion_workflow import create_design
from systems.contracts.results import CalculationResult, ResultStatus
from systems.visualization.plots import design_plots, simulation_plots


def source_design():
    design = create_design(name="Synthetic plot contract only")
    result = CalculationResult(calculation_type="nozzle.tangent_bell", status=ResultStatus.CURRENT,
        outputs={"stations": [{"x_m": x, "radius_m": .01 + x, "mach": 1 + x,
            "pressure_pa": 3e6, "temperature_k": 3500} for x in (0., .01, .02)]})
    design.workflow.store_result("nozzle", result)
    return design


def test_current_units_identity_exact_rows_and_no_mutation():
    design = source_design(); before = deepcopy(design.to_canonical_dict())
    value = design_plots(design)
    assert len(value["plots"]) == 4
    plot = value["plots"][0]
    assert plot["x"] == {"label": "Axial position", "unit": "m"}
    assert plot["y"]["unit"] == "m" and plot["series"][0]["points"][0][0] == 0
    assert len(plot["source"]["content_sha256"]) == 64 and plot["uncertainty"] == "not quantified"
    assert hashlib.sha256(plot["source"]["source_canonical_json"].encode()).hexdigest() == plot["source"]["content_sha256"]
    assert json.loads(plot["source"]["source_canonical_json"]) == plot["source"]["source_record"]
    plot["rows"][0]["x_m"] = 123
    assert design.to_canonical_dict() == before


def test_stale_is_not_current():
    design = source_design(); design.workflow.results["nozzle"].mark_stale()
    value = design_plots(design)
    assert not value["plots"] and value["unavailable"][0]["status"] == "STALE"


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, "1"])
def test_invalid_values_are_not_silently_dropped(bad):
    design = source_design(); design.workflow.results["nozzle"].outputs["stations"][1]["x_m"] = bad
    try:
        value = design_plots(design)
        assert not value["plots"] and any(row["status"] == "INVALID_DATA" for row in value["unavailable"])
    except ValueError:
        pass  # Canonical non-finite hashes fail closed before projection.


def test_radial_reference_residual_and_signed_balance():
    dataset = {"schema_version": "p09-dataset-v1", "run_id": "synthetic", "study_id": "synthetic",
        "execution_status": "completed", "solution_verification": "fixture", "experimental_validation": "not-performed",
        "study": {"model": "steady-spherical-conduction-v1"},
        "numerical_convergence": "converged", "conservation_checks": {}, "source_refs": [], "diagnostics": [],
        "radii_m": [0.001, .002], "temperature_k": [301., 300.], "reference_k": [301., 300.],
        "iterations": [0, 1], "normalized_residuals": [1., 0.], "power_imbalance_w": [-1., 0.],
        "residual_definition": "L2(b-A(T-Ts))/L2(b); b=qV"}
    plots = simulation_plots(dataset)["plots"]
    assert len(plots) == 3 and plots[0]["series"][1]["role"] == "reference"
    assert plots[2]["series"][0]["points"] == [[0, -1.], [1, 0.]]
    assert "L2" in plots[1]["notes"][0]
