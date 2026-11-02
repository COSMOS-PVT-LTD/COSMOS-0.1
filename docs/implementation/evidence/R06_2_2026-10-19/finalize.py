"""Bind completed local R06.2a checks to additive source identities only."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections import Counter
from hashlib import sha256

from record import HERE, ROOT, sources

ADDITIONS = {
    "physics/feed/__init__.py", "physics/feed/pressure_fed.py",
    "systems/cycle/pressure_fed.py", "api/pressure_fed.py",
    "tests/unit_tests/physics/test_pressure_fed.py",
    "tests/unit_tests/systems_layer/test_pressure_fed_assessment.py",
}


def main() -> None:
    entry = json.loads((HERE / "entry.json").read_text())
    current = sources()
    changed = [name for name, digest in entry["sha256"].items() if current.get(name) != digest]
    assert not changed, changed
    assert set(current) - set(entry["sha256"]) == ADDITIONS
    suites = ET.parse(HERE / "full-qualified.xml").getroot()
    assert not list(suites.iter("failure")) and not list(suites.iter("error"))
    cases = list(suites.iter("testcase"))
    assert len(cases) > 3300  # an interrupted subset cannot qualify the whole suite
    focused = ET.parse(HERE / "focused-final.xml").getroot()
    assert not list(focused.iter("failure")) and not list(focused.iter("error"))
    assert len(list(focused.iter("testcase"))) == 121
    assert "All checks passed!" in (HERE / "ruff-qualified.log").read_text()
    assert "Success:" in (HERE / "mypy-qualified.log").read_text()
    assert "pass 402" in (HERE / "js-final.log").read_text()
    assert "fail 0" in (HERE / "js-final.log").read_text()
    assert "76 passed" in (HERE / "isolation-order.log").read_text()
    assert not (HERE / "whitespace-final.log").read_bytes()
    preservation = json.loads((HERE / "preservation-final.json").read_text())
    assert preservation["pass"]
    example = json.loads((HERE / "example-result.json").read_text())
    original_bytes = (HERE / "example-baseline.json").read_bytes()
    example_inputs = example["result"]["inputs"]
    assert original_bytes == example_inputs["baseline_canonical_text"].encode()
    assert sha256(original_bytes).hexdigest() == example_inputs["baseline_sha256"]
    assert json.loads((HERE / "example-input.json").read_text()) == example_inputs["specification"]
    assert all(current[name] == digest for name, digest in example["method_sources"].items())
    assert example["result"]["outputs"]["assessment_balances_closed_within_declared_tolerances"]
    assert not example["result"]["outputs"]["workflow_cycle_complete"]
    passed = sum(t.find("skipped") is None for t in cases)
    skipped = len(list(suites.iter("skipped")))
    result = {
        "phase": "R06", "status": "PARTIAL", "slice": "R06.2a_pressure_fed_computational_foundation",
        "slice_status": "PASS_LOCAL_DECLARED_SCOPE", "head": entry["head"],
        "baseline_passed": 27, "independent_physics_passed_before_integration": 52,
        "focused_passed": 121, "new_tests_passed": 116, "import_isolation_regression_passed": 76,
        "python": {"passed": passed, "skipped": skipped,
                   "skip_reasons": dict(Counter(t.attrib.get("message", "") for t in suites.iter("skipped")))},
        "javascript_passed": 402, "ruff": "PASS", "mypy_source_files": 387,
        "preceding_source_count": len(entry["sha256"]), "preceding_sources_changed": changed,
        "additions": sorted(ADDITIONS), "existing_scientific_sources_unchanged": True,
        "old_inventory": {"unchanged": preservation["unchanged"],
                          "declared_changes": len(preservation["declared_phase_changes"]),
                          "unexpected": len(preservation["unexpected_changes"]),
                          "missing": len(preservation["missing"])},
        "requirements": {"RKT-01": "PARTIAL_PRIOR_SENSITIVITY_SLICE",
                         "RKT-02": "PARTIAL_COMPUTATIONAL_FOUNDATION",
                         "RKT-03": "PARTIAL_SPECIFIED_FLOW_LIQUID_BUDGET_ONLY",
                         "RKT-04": "APPROVED_PLANNED_AFTER_PRESSURE_FED_INTEGRATION",
                         "RKT-05": "OUTSIDE_SELECTED_SCOPE_UNSUPPORTED",
                         "RKT-06": "OUTSIDE_SELECTED_SCOPE_UNSUPPORTED",
                         "RKT-07": "OUTSIDE_SELECTED_SCOPE_UNSUPPORTED",
                         "RKT-08": "OPEN_SUBSYSTEM_DIVERSION_COUPLING"},
        "workflow_cycle_promoted": False, "managed_http_ui_integration": "NOT_YET_IMPLEMENTED",
        "cea_adapter": "REFUSED_PENDING_QUALIFICATION", "pressurant": "IMPOSED_BOUNDARY_ONLY",
        "actual_api_example_original_bytes_and_method_hashes": "PASS_SYNTHETIC_SOFTWARE_ONLY",
        "browser_native_qualification": "NOT_RUN_API_ONLY_SLICE", "physical_validation": "NOT_PERFORMED",
        "live_owner_data_changed": False, "commit_push_release": False,
        "next": "R06.2b managed pressure-fed history/HTTP/UI and explicit workflow dependency design, then R06.3 gas-generator",
    }
    for name, data in (("STATUS.json", result), ("source-final.json", {
        "scope": "R06.2a local source identities, not release or physical seal",
        "head": entry["head"], "sha256": current,
        "preceding_source_parity": True,
    })):
        with (HERE / name).open("x") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
    print(json.dumps({"phase": "PARTIAL", "slice": result["slice_status"], "python_passed": passed,
                      "python_skipped": skipped, "previous_sources_unchanged": len(entry["sha256"]),
                      "source_additions": len(ADDITIONS), "root": str(ROOT)}))


if __name__ == "__main__":
    main()
