"""Seal P11 executed software evidence; never confer human/physical acceptance."""
import hashlib
import io
import json
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from api.ngg_workbench import runtime_config
from simulation.contracts import StudySnapshot
from systems.contracts.geometry._wire import digest, dumps
from validation.reporting import EngineeringReports

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SEAL = HERE / "artifact_hashes.json"


def filehash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def save(name, value):
    target = HERE / name
    with target.open("x") as output:
        output.write(json.dumps(value, indent=2) + "\n")


def pytest_result(name):
    suites = list(ET.parse(HERE / name).getroot().iter("testsuite"))
    assert suites and all(int(s.attrib["failures"]) == int(s.attrib["errors"]) == 0 for s in suites), name
    skipped = sum(int(s.attrib["skipped"]) for s in suites)
    return {"passed": sum(int(s.attrib["tests"]) for s in suites) - skipped, "skipped": skipped}


def preservation():
    baseline = read("baseline.json")
    expected_changed = {"gui/server.py", ".github/workflows/ci.yml"}
    changed = [name for name, expected in baseline["sha256"].items()
               if not (ROOT / name).is_file() or filehash(ROOT / name) != expected]
    assert set(changed) == expected_changed, changed
    for name in expected_changed:
        assert filehash(HERE / "before" / name) == baseline["sha256"][name], name
    cache = "cache/cea/test_key.json"
    assert filehash(ROOT / cache) == filehash(HERE / "before" / cache) == baseline["sha256"][cache]
    assert filehash(ROOT / cache) == "6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508"
    predecessor_path = HERE.parent / "P10_2026-10-11/artifact_hashes.json"
    predecessor = json.loads(predecessor_path.read_text())
    assert len(predecessor) == baseline["predecessor_sealed_files"] == 3116
    for name, expected in predecessor.items():
        path = HERE / "before" / name if name in expected_changed else ROOT / name
        assert filehash(path) == expected, name
    assert filehash(predecessor_path) == baseline["sha256"][str(predecessor_path.relative_to(ROOT))]
    return ({"pass": True, "baseline_files": len(baseline["sha256"]), "only_changed": sorted(changed),
             "unrelated_work_preserved": True, "synthetic_test_cache_exactly_restored": True,
             "baseline_commit_sha": baseline["commit_sha"]},
            {"pass": True, "predecessor_files": len(predecessor), "before_overlay": sorted(expected_changed),
             "historical_seal_unmodified": True})


def provenance():
    receipt = read("report-fixture.json")
    report = receipt["report"]
    raw = receipt["canonical_json"].encode()
    report_id = receipt["report_id"]
    assert hashlib.sha256(raw).hexdigest() == report_id == read("provenance-integrity.json")["report_sha256"]
    assert json.loads(raw) == report and (HERE / "report.json").read_bytes() == raw
    dataset = read("p09-dataset.json")
    comparison = read("p10-comparison.json")
    native = read("native-source.json")
    assert digest(dataset) == report["dataset_sha256"] == comparison["report"]["candidate"]["provenance"]["source_sha256"]
    assert json.loads(report["dataset_canonical_json"]) == dataset
    assert report["comparison_canonical_json"] == comparison["canonical_json"]
    assert hashlib.sha256(comparison["canonical_json"].encode()).hexdigest() == report["comparison_receipt_id"] == comparison["report_id"]
    assert json.loads(comparison["canonical_json"]) == comparison["report"]
    study = StudySnapshot.from_json(dumps(dataset["study"]))
    assert study.content_sha256 == dataset["study_id"] == report["input_revision"]
    assert report["run_id"] == dataset["run_id"] and native["job_id"] == report["geometry_job_id"]
    assert study.handoff.geometry_snapshot_id == report["geometry_snapshot_id"] == native["snapshot_id"]
    assert native["state"] == "accepted" and native["byte_integrity"] and native["qa"]["qa-step"]["pass"]
    assert hashlib.sha256(report["geometry_qa_canonical_json"].encode()).hexdigest() == report["geometry_qa_sha256"] == study.handoff.integrity_sha256
    assert json.loads(report["geometry_qa_canonical_json"]) == native["qa"]
    artifact = report["geometry_artifact"]
    assert artifact == native["record"]["artifacts"][0]
    assert filehash(HERE / "native-handoff/export.step") == artifact["sha256"]
    assert filehash(HERE / "native-handoff/source.brep") == artifact["source_artifact_sha256"]
    for source in [*report["reproducibility"]["source_refs"], report["reproducibility"]["renderer_source"]]:
        assert filehash(ROOT / source["path"]) == source["sha256"], source["path"]
    for claim in [read("source-to-claim.json"), *report["claims"]]:
        assert hashlib.sha256(claim["canonical_json"].encode()).hexdigest() == claim["evidence_sha256"]
        assert json.loads(claim["canonical_json"]) == claim["claim"]
        source = claim["claim"]["source"]
        assert source["source_origin"] == "synthetic-contract-fixture"
        assert filehash(HERE / "synthetic-source-original.txt") == source["sha256"]
    assert report["status"]["experimental_validation"] == "not-performed"
    assert report["status"]["independent_acceptance"] is report["status"]["production_handoff"] is False
    signoff = read("signoff-report.json")
    assert not signoff["signed_human_approval"] and signoff["production_handoff"] == "BLOCKED"
    assert signoff["review_intents"] and all(i["independent_acceptance"] is False for i in signoff["review_intents"])
    archive = (HERE / "review-package.zip").read_bytes()
    assert archive == (HERE / "downloaded-review-package.zip").read_bytes()
    assert hashlib.sha256(archive).hexdigest() == read("provenance-integrity.json")["package_sha256"]
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        assert package.testzip() is None and set(package.namelist()) == {"report.json", "report.md", "report.html", "manifest.json"}
        manifest = json.loads(package.read("manifest.json"))
        assert manifest["report_id"] == report_id and manifest["production_handoff"] is False
        assert set(manifest["files"]) == {"report.json", "report.md", "report.html"}
        for name, expected in manifest["files"].items():
            assert hashlib.sha256(package.read(name)).hexdigest() == expected
            assert package.read(name) == (HERE / name).read_bytes()
    # Offline rerender of exact retained canonical bytes, not a solver rerun or publication.
    service = EngineeringReports()
    service.session(report["actor"]).reports[report_id] = raw
    for name, value in service.files(report["actor"], report_id).items():
        assert value == (HERE / name).read_bytes(), name
    assert service.package(report["actor"], report_id) == archive
    return {"pass": True, "exact_canonical_report": True, "native_source_export_bytes": True,
            "dataset_receipt_qa_source_renderer_checks": True, "manifest_files": 3,
            "offline_rerender_byte_identical": True, "source_fixture": "explicit synthetic contract evidence",
            "physical_validation": False, "signed_acceptance": False}


def checks():
    python = pytest_result("python-final2.xml")
    focused = pytest_result("focused-final2.xml")
    assert python == {"passed": 2736, "skipped": 76}
    assert focused == {"passed": 51, "skipped": 0}
    assert pytest_result("baseline-tests.xml") == {"passed": 2685, "skipped": 76}
    browser = read("browser-tests.json")["stats"]
    assert browser["expected"] == 11 and browser["unexpected"] == browser["flaky"] == browser["skipped"] == 0
    javascript = (HERE / "javascript-final2.log").read_text()
    assert re.search(r"pass 132\b", javascript) and re.search(r"fail 0\b", javascript)
    assert "All checks passed!" in (HERE / "ruff-final2.log").read_text()
    assert "Success: no issues found in 347 source files" in (HERE / "mypy-final2.log").read_text()
    assert not (HERE / "display-contracts-final2.log").read_text().strip()
    for theme in ("dark", "high-contrast"):
        assert not read("accessibility-" + theme + ".json")["violations"]
        assert not read("accessibility-final-" + theme + ".json")["violations"]
    for row in read("performance.json"):
        assert row["scrollWidth"] <= row["width"] and row["tableRows"] == 5
    final_views = read("final-view-checks.json")
    assert final_views["pass"] and final_views["unchanged_report_history"] and final_views["themeViolations"] == 0
    assert {row["width"] for row in final_views["checks"]} == {1440, 1024, 390}
    assert all(row["scrollWidth"] <= row["width"] and row["unitHeaderWhitespace"] == "nowrap" for row in final_views["checks"])
    parity = read("physics_parity.json")
    assert parity["pass"] and parity["cases"] == 5 and parity["tolerance"] == 0
    assert read("physics_after.json") == json.loads((HERE.parent / "P10_2026-10-11/physics_after.json").read_text())
    assert filehash(HERE.parent / "P10_2026-10-11/physics_after.json") == parity["baseline_sha256"]
    assert read("provenance-integrity.json")["pass"]
    proof = provenance()
    return {"python": python, "p11_focused_included_in_python": focused, "javascript_passed": 132,
            "browser_passed": 11, "actual_native_flow": "OCCT sphere to P09 finite-volume run to P10 analytic comparison to report",
            "final_css_readonly_layout_checks": 3, "axe_violations": {"dark": 0, "high-contrast": 0},
            "physics_parity_cases": 5, "ruff": "PASS", "mypy_files": 347, "strict_display_contracts": "PASS",
            "report_integrity": proof, "remote_ci_executed": False, "experimental_validation": False}


def main():
    runtime_config((HERE.parent / "P08_2026-10-09/local-runtime.json").resolve())
    if sys.argv[1:] == ["--verify"]:
        hashes = read("artifact_hashes.json")
        for name, expected in hashes.items():
            assert filehash(ROOT / name) == expected, name
        summary = checks()
        preservation()
        print(json.dumps({"evidence_integrity": "PASS", "sealed_files": len(hashes), "P11_software": "PASS",
                          "report_rerender": summary["report_integrity"]["offline_rerender_byte_identical"],
                          "production_handoff": False, "experimental_validation": False, "human_acceptance": False}))
        return
    assert not sys.argv[1:], "Only --verify is supported"
    assert not SEAL.exists(), "Do not replace sealed evidence; create a reproduction overlay"
    summary = checks()
    source_integrity, predecessor_integrity = preservation()
    commands = [
        ".venv-remediation/bin/python -m pytest -q --junitxml=docs/implementation/evidence/P11_2026-10-11/python-final2.xml",
        ".venv-remediation/bin/python -m pytest tests/unit_tests/knowledge/test_evidence_navigation.py tests/unit_tests/validation/test_reporting.py tests/integration_tests/gui/test_knowledge_reports_http.py -q",
        "/opt/homebrew/bin/node --test tests/js/*.test.cjs",
        "NODE_PATH=/private/tmp/cosmos-p03.pfPm6s/node_modules /opt/homebrew/bin/node /private/tmp/cosmos-p03.pfPm6s/node_modules/@playwright/test/cli.js test --config=tests/ui/knowledge_reports/playwright.config.cjs",
        ".venv-remediation/bin/python -m ruff check core knowledge physics numerics systems simulation validation api gui infrastructure plugins tests tools",
        ".venv-remediation/bin/python -m mypy core physics numerics systems api simulation validation knowledge/workspace/evidence_navigation.py",
        "/opt/homebrew/bin/node /private/tmp/cosmos-p03.pfPm6s/node_modules/typescript/bin/tsc --noEmit --strict --target ES2020 --module Node16 --moduleResolution Node16 tests/ui/knowledge_reports/type_contracts.ts",
        "PYTHONPATH=. .venv-remediation/bin/python docs/implementation/evidence/P11_2026-10-11/collect_evidence.py",
        "NODE_PATH=/private/tmp/cosmos-p03.pfPm6s/node_modules /opt/homebrew/bin/node docs/implementation/evidence/P11_2026-10-11/final_view_checks.cjs",
        "PYTHONPATH=. .venv-remediation/bin/python docs/implementation/evidence/P11_2026-10-11/finalize_evidence.py",
    ]
    gate = {"gate_id": "P11_SOFTWARE", "phase": "P11_KNOWLEDGE_REPORTS", "decision": "SOFTWARE_PASS",
            "software_pass": True, "date": "2026-10-11",
            "commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
            "working_tree_evidence": "Preserved dirty-tree baseline, two-file before overlay and artifact_hashes.json; not a published Git revision",
            "environment": {"os": platform.system(), "architecture": platform.machine(), "python": platform.python_version(),
                            "node": "26.7.0", "browser": "Local actual Google Chrome", "runtime": "Qualified local P08 OCCT manifest; predecessor proof preserved"},
            "scope": "Existing-source knowledge navigation and actual steady spherical research report preview, not arbitrary engine qualification",
            "requirement_ids": ["GOV-001", "GOV-003", "GOV-004", "GOV-005", "GOV-007", "GOV-008", "GOV-009",
                                "UX-001", "UX-002", "UX-003", "UX-004", "UX-005", "UX-006", "UX-007", "T-011", "T-012", "T-015", "T-017"],
            "commands": commands, "tests": summary,
            "test_artifacts": ["python-final2.xml", "focused-final2.xml", "javascript-final2.log", "browser-tests.json",
                               "accessibility-final-dark.json", "accessibility-final-high-contrast.json", "final-view-checks.json",
                               "source-to-claim.json", "report.json", "review-package.zip", "provenance-integrity.json",
                               "source_integrity.json", "predecessor_integrity.json", "physics_parity.json", "signoff-report.json"],
            "reviewer": "Codex automated scoped software assessment; not qualified independent engineering acceptance",
            "formal_human_acceptance": False, "experimental_validation": False, "production_handoff": False,
            "default_enabled": False, "engineering_publication": False, "remote_ci_executed": False,
            "blockers": {"scoped_software_phase": [], "physical_and_production": [
                "No authentic measured experiment or qualified independent acceptance recorded",
                "Durable signed engineering publication and full uncertainty evidence are outside this preview",
                "P12/G9 remote CI, packaging, SBOM/license, security and operational release evidence pending"]},
            "limits": ["Synthetic knowledge records test source/review contracts, not approved science",
                       "Native execution is the bounded OCCT sphere/P09/P10 fixture, not engine physical validation",
                       "Reports are ephemeral actor-owned previews; retain downloaded immutable packages before restart"],
            "next": "P12_RELEASE_HARDENING", "p12_readiness": "Research-tool release hardening only", "p12_executed": False}
    assert gate["commit_sha"] == source_integrity["baseline_commit_sha"]
    save("source_integrity.json", source_integrity)
    save("predecessor_integrity.json", predecessor_integrity)
    save("test-summary.json", summary)
    save("P11_GATE.json", gate)
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    # Explicit retained native bytes, logs and images may match repository ignore rules.
    names += [str(p.relative_to(ROOT)) for p in HERE.rglob("*") if p.is_file()]
    hashes = {name: filehash(ROOT / name) for name in sorted(set(names))
              if name and (ROOT / name).is_file() and ROOT / name != SEAL and "__pycache__" not in Path(name).parts}
    save("artifact_hashes.json", hashes)
    print(json.dumps({"P11_software": "PASS", "sealed_files": len(hashes), "tests": summary,
                      "experimental_validation": False, "production_handoff": False}))


if __name__ == "__main__":
    main()
