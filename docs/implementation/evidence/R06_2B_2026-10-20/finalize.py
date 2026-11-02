"""Bind local R06.2b test/UI evidence to the exact additive candidate."""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections import Counter
from hashlib import sha256

from record import HERE, sources

EDITS = {"api/context_projects.py", "api/project_authority.py", "gui/server.py",
         "gui/static/projects.js", "gui/static/rocket-workbench/view.js"}
ADDITIONS = {"systems/projects/pressure_fed.py", "api/pressure_fed_projects.py",
             "gui/static/managed-pressure-fed.js", "gui/static/managed-pressure-fed.css",
             "tests/unit_tests/infrastructure/test_managed_pressure_fed.py",
             "tests/integration_tests/gui/test_pressure_fed_projects_http.py",
             "tests/js/managed_pressure_fed.test.cjs", "tests/ui/r06_2b/preview.py",
             "tests/ui/r06_2b/check_exports.py"}


def main() -> None:
    entry = json.loads((HERE / "entry.json").read_text())
    current = sources()
    changed = {name for name, digest in entry["sha256"].items() if current.get(name) != digest}
    assert changed == EDITS, changed ^ EDITS
    assert set(current) - set(entry["sha256"]) == ADDITIONS
    assert not any(name.startswith(("core/", "physics/", "numerics/", "systems/")) for name in changed)
    suites = ET.parse(HERE / "full-python.xml").getroot()
    assert not list(suites.iter("failure")) and not list(suites.iter("error"))
    cases = list(suites.iter("testcase"))
    passed = sum(t.find("skipped") is None for t in cases)
    assert passed == 3415
    focused = ET.parse(HERE / "focused-final.xml").getroot()
    assert not list(focused.iter("failure")) and len(list(focused.iter("testcase"))) == 23
    assert "All checks passed!" in (HERE / "ruff-final.log").read_text()
    assert "Success:" in (HERE / "mypy-final.log").read_text()
    assert "pass 408" in (HERE / "js-final.log").read_text() and "fail 0" in (HERE / "js-final.log").read_text()
    assert not (HERE / "typescript-qualified.log").read_bytes()
    assert not (HERE / "whitespace-final.log").read_bytes()
    preservation = json.loads((HERE / "preservation-final.json").read_text())
    assert preservation["pass"]
    proof = json.loads((HERE / "export-proof-final.json").read_text())
    original = (HERE / "ui-final-record.json").read_bytes()
    assert original == (HERE / "ui-restart-record.json").read_bytes()
    assert sha256(original).hexdigest() == proof["canonical_sha256"]
    record = json.loads(original)
    assert all(current[name] == digest for name, digest in record["method_sources"].items())
    restart = (HERE / "ui-final-restart-qualified.txt").read_text()
    assert proof["commit_id"] in restart and proof["canonical_sha256"] in restart
    assert "Baseline and method sources current" in restart
    assert "Choose an exact saved propulsion baseline first" in (HERE / "ui-empty-input-refusal.txt").read_text()
    assert "HISTORICAL baseline or method sources" in (HERE / "ui-historical-methods.txt").read_text()
    assert "upstream current" in (HERE / "ui-final-lineage.txt").read_text()
    assert not any(row["level"] == "error" for row in json.loads((HERE / "browser-console-final.json").read_text()))
    result = {
        "phase": "R06", "status": "PARTIAL", "slice": "R06.2b_managed_pressure_fed_assessment",
        "slice_status": "PASS_LOCAL_DECLARED_SCOPE", "head": entry["head"],
        "baseline_passed": 122, "new_authority_http_tests_passed": 23,
        "python": {"passed": passed, "skipped": len(list(suites.iter("skipped"))),
                   "skip_reasons": dict(Counter(s.attrib.get("message", "") for s in suites.iter("skipped")))},
        "javascript_passed": 408, "new_javascript_tests": 6, "ruff": "PASS",
        "mypy_source_files": 389, "strict_typescript_consumers": 7,
        "source_preservation": {"preceding": len(entry["sha256"]), "unchanged": len(entry["sha256"])-len(changed),
                                "declared_edits": sorted(changed), "additions": sorted(ADDITIONS)},
        "old_inventory": {"unchanged": preservation["unchanged"], "declared_changes": len(preservation["declared_phase_changes"]),
                          "unexpected": len(preservation["unexpected_changes"]), "missing": len(preservation["missing"])},
        "existing_core_physics_numerics_systems_sources_unchanged": True,
        "actual_browser_source_downloads_restart": "PASS", "actual_subprocess_kill_after_input_capture": "PASS",
        "final_example": {"project_id": proof["project_id"], "object_id": proof["object_id"],
                          "commit_id": proof["commit_id"], "source_sha256": proof["canonical_sha256"]},
        "workflow_cycle_promoted": False, "new_storage_schema_or_dependency": False,
        "cea_pressure_fed_adapter": "UNSUPPORTED", "pressurant": "IMPOSED_BOUNDARY_ONLY",
        "actual_injector_cooling_film_diversion_coupling": "NOT_ASSESSED",
        "native_cocoa_and_human_qualification": "NOT_RUN", "physical_validation": "NOT_PERFORMED",
        "live_owner_data_changed": False, "commit_push_release": False,
        "requirements": {"RKT-01": "PARTIAL_PRIOR_SENSITIVITY_SCOPE", "RKT-02": "PARTIAL_SPECIFIED_FLOW_ASSESSMENT",
                         "RKT-03": "PARTIAL_LIQUID_BUDGET_BOUNDARY_ONLY_MANAGED_INTEGRATION_VERIFIED",
                         "RKT-04": "APPROVED_NEXT_GAS_GENERATOR_CONTRACTS", "RKT-08": "OPEN_SUBSYSTEM_COUPLING"},
        "next": "R06.3 primary-source gas-generator model/reference contracts before pump/turbine/diversion/power implementation",
    }
    for name, data in (("STATUS.json", result), ("source-final.json", {
        "scope": "R06.2b local test/UI source identities only; not a release/physical seal",
        "head": entry["head"], "sha256": current,
    })):
        with (HERE / name).open("x") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
    print(json.dumps({"slice": result["slice_status"], "phase": result["status"], "python_passed": passed,
                      "previous_sources_unchanged": len(entry["sha256"])-len(changed),
                      "declared_existing_edits": len(changed), "additions": len(ADDITIONS)}))


if __name__ == "__main__":
    main()
