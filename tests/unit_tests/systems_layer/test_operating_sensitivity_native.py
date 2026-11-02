"""Real NASA CEA coupled cases, never hardware validation."""

import pytest

pytest.importorskip("cea", reason="Pinned NASA CEA required; analytic sensitivity tests run separately")

from systems.cycle.operating_sensitivity import study
from tests.fixtures.engine_operating import design, specification
from tests.fixtures.engineering_extensions import sensitivity
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


@pytest.mark.parametrize("cycle", ["PRESSURE_FED", "GAS_GENERATOR"])
def test_each_case_recomputes_native_chamber_network_and_thermal_candidate(cycle):
    baseline = design(cycle)
    recipe, _ = specification(baseline, cooling=True)
    spec = sensitivity(recipe)
    out = study(baseline, spec).outputs
    assert out["study_status"] == "COMPLETED"
    assert all(d["status"] == "AVAILABLE" for d in out["derivatives"])
    assert len(out["evaluations"]) == 5
    assert len({row["result"]["outputs"]["candidate"]["core"]["gas"]["temperature_k"] for row in out["evaluations"]}) == 5
    assert len({row["output"] for row in out["evaluations"]}) == 5
    for row in out["evaluations"]:
        assert all(r["passed"] for r in row["result"]["outputs"]["residuals"])
        assert row["result"]["outputs"]["candidate"]["cooling"]["total_heat_w"] > 0
