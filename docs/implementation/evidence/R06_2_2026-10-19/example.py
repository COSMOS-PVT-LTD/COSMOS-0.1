"""Reproducible synthetic API example, not owner/hardware data or publication."""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from api.pressure_fed import assess_pressure_fed  # noqa: E402


def main() -> None:
    fixtures = runpy.run_path(str(ROOT / "tests/unit_tests/systems_layer/test_pressure_fed_assessment.py"))
    # Fresh process uses real existing model evaluation. This fixture builder is
    # not an engine data loader; synthetic inputs are explicitly labelled.
    design = fixtures["baseline"].__wrapped__()
    spec = fixtures["specification"](design)
    original = design.to_canonical_json()
    outcome = assess_pressure_fed(design, spec)
    assert design.to_canonical_json() == original
    outputs = outcome["result"]["outputs"]
    assert outputs["assessment_balances_closed_within_declared_tolerances"]
    assert not outputs["workflow_cycle_complete"]
    for name, data in (("example-baseline.json", json.loads(original)),
                       ("example-input.json", spec), ("example-result.json", outcome)):
        text = original if name == "example-baseline.json" else json.dumps(data, indent=2, allow_nan=False)
        with (HERE / name).open("x") as stream:
            stream.write(text)
            if not text.endswith("\n") and name != "example-baseline.json":
                stream.write("\n")
    print(json.dumps({
        "fixture": "SYNTHETIC_SOFTWARE_ONLY", "source_unchanged": True,
        "core_mass_flow_kg_s": outputs["total_core_mass_flow_kg_s"],
        "pressure_states": {name: row["pressure_state"] for name, row in outputs["streams"].items()},
        "workflow_cycle_complete": False, "physical_validation": "NOT_PERFORMED",
    }))


if __name__ == "__main__":
    main()
