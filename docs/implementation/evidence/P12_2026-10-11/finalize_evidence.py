"""Seal executed local P12 evidence while keeping production G9 blocked."""
import hashlib
import importlib.metadata
import io
import json
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SEAL = HERE / "artifact_hashes.json"
sys.path.insert(0, str(ROOT))
from infrastructure.release.inventory import canonical, contract_registry, sha, source_files, verify_registry
from packaging.requirements import Requirement
from validation.reporting import EngineeringReports

EXISTING_CHANGED = {".github/workflows/ci.yml", ".gitignore", "SECURITY.md", "api/authentication.py", "gui/server.py",
                    "gui/static/app.js", "gui/static/rbac.js", "scripts/build_macos_app.sh"}
PLAN = str((HERE / "PLAN.md").relative_to(ROOT))


def read(name):
    return json.loads((HERE / name).read_text())


def save(name, value):
    with (HERE / name).open("x") as handle:
        handle.write(json.dumps(value, indent=2) + "\n")


def tree(path):
    return {str(p.relative_to(path)): sha(p) for p in sorted(path.rglob("*")) if p.is_file()}


def preservation():
    baseline = read("baseline.json")
    changed = {n for n, h in baseline["sha256"].items() if not (ROOT / n).is_file() or sha(ROOT / n) != h}
    assert changed == EXISTING_CHANGED | {PLAN}, sorted(changed)
    for name in changed:
        backup = HERE / "before" / ("PLAN.md" if name == PLAN else name)
        assert sha(backup) == baseline["sha256"][name], name
    cache = "cache/cea/test_key.json"
    assert sha(ROOT / cache) == sha(HERE / "before" / cache) == baseline["sha256"][cache]
    assert sha(ROOT / cache) == "6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508"
    assert tree(ROOT / "dist/COSMOS 0.1.app") == baseline["existing_mac_app"]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    assert head == baseline["commit_sha"]
    predecessor_path = HERE.parent / "P11_2026-10-11/artifact_hashes.json"
    prior = json.loads(predecessor_path.read_text())
    assert len(prior) == baseline["predecessor_sealed_files"] == 3202
    for name, expected in prior.items():
        candidate = HERE / "before" / name if name in EXISTING_CHANGED else ROOT / name
        assert sha(candidate) == expected, name
    assert sha(predecessor_path) == baseline["sha256"][str(predecessor_path.relative_to(ROOT))]
    return ({"pass": True, "baseline_files": len(baseline["sha256"]), "only_changed": sorted(changed),
             "existing_product_governance_files_changed": len(EXISTING_CHANGED), "unchanged_original_app_files": len(baseline["existing_mac_app"]),
             "synthetic_cache_exactly_restored": True, "unrelated_work_preserved": True, "commit_sha": head},
            {"pass": True, "predecessor_sealed_files": len(prior), "historical_evidence_unmodified": True,
             "exact_before_overlay": sorted(EXISTING_CHANGED), "P11_seal_sha256": sha(predecessor_path)})


def pytest(name):
    root = ET.parse(HERE / name).getroot()
    suites = list(root.iter("testsuite"))
    assert suites and all(int(s.attrib["failures"]) == int(s.attrib["errors"]) == 0 for s in suites), name
    skip = sum(int(s.attrib["skipped"]) for s in suites)
    skipped = [{"test": t.attrib.get("classname", "") + "." + t.attrib["name"], "reason": t.find("skipped").attrib.get("message", "")}
               for t in root.iter("testcase") if t.find("skipped") is not None]
    return {"passed": sum(int(s.attrib["tests"]) for s in suites) - skip, "skipped": skip,
            "skipped_tests": skipped, "skip_reason_counts": dict(Counter(t["reason"] for t in skipped)), "artifact": name}


def package():
    value = read("package-integrity.json")
    app = Path(value["app"])
    assert value["pass"] and value["files"] == tree(app)
    manifest = read("package-source-manifest.json")
    assert manifest["source_files"] == source_files(ROOT)
    assert sha(Path(manifest["external_python"])) == value["external_python_sha256"] == manifest["external_python_sha256"]
    registry = read("frozen-contract-registry.json")
    verify_registry(ROOT, registry)
    assert registry == contract_registry(ROOT) == read("inventory-release-final/frozen-contract-registry.json")
    assert registry == json.loads((app / "Contents/Resources/frozen-contract-registry.json").read_text())
    assert value["signing"]["identity"] == "ad-hoc" and not value["signing"]["developer_id"] and not value["signing"]["notarized"]
    result = subprocess.run(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(app)], capture_output=True)
    assert result.returncode == 0
    unsigned = read("unsigned-payload.json")
    assert unsigned["files"] == tree(Path(unsigned["reproduction"]))
    return {"pass": True, "source_files": len(manifest["source_files"]), "frozen_files": len(registry["files"]),
            "local_adhoc_integrity": True, "unsigned_reproduction": True, "standalone": False,
            "developer_id": False, "notarized": False, "trusted_distribution": False}


def inventory():
    summary = read("inventory-release-final/inventory-summary.json")
    assert summary["sbom_schema_valid"] and summary["components"] == 208 and summary["python_distributions"] == 97
    assert summary["native_files_verified"] == 99 and not summary["distribution_approved"]
    base = HERE / "inventory-release-final"
    from jsonschema import Draft7Validator
    from referencing import Registry, Resource
    schemas = {name: json.loads((base / "schema" / name).read_text())
               for name in ("bom-1.5.schema.json", "spdx.schema.json", "jsf-0.82.schema.json")}
    resources = [(scheme + "://cyclonedx.org/schema/" + name, Resource.from_contents(value))
                 for scheme in ("http", "https") for name, value in schemas.items()]
    Draft7Validator(schemas["bom-1.5.schema.json"], registry=Registry().with_resources(resources)).validate(read("inventory-release-final/sbom.cdx.json"))
    native = read("runtime-config.json")
    for name, expected in native["sha256"].items():
        assert sha(Path(name)) == expected, name
    file_count = 0
    for item in read("inventory-release-final/installed-file-integrity.json").values():
        for name, expected in item["files_sha256"].items():
            assert sha(Path(item["environment"]) / name) == expected, name
            file_count += 1
    for line in (ROOT / "requirements-release-macos.txt").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            requirement = Requirement(line.strip())
            if requirement.marker is None or requirement.marker.evaluate():
                assert requirement.specifier.contains(importlib.metadata.version(requirement.name)), requirement.name
    return {"pass": True, "components": 208, "installed_distributions": 97, "installed_files_verified": file_count,
            "native_files_verified": 99, "schema_validated_offline": True, "distribution_approved": False}


def provenance():
    value = read("packaged-report.json")
    report = value["report"]
    raw = value["canonical_json"].encode()
    assert hashlib.sha256(raw).hexdigest() == value["report_id"] and json.loads(raw) == report
    assert read("provenance-integrity.json")["pass"]
    assert not report["status"]["production_handoff"] and not report["status"]["independent_acceptance"]
    assert report["status"]["experimental_validation"] == "not-performed" and report["claims"] == []
    native = report["geometry_artifact"]
    assert sha(HERE / "packaged-native-handoff/source.brep") == native["source_artifact_sha256"]
    assert sha(HERE / "packaged-native-handoff/export.step") == native["sha256"]
    archive = (HERE / "packaged-review-package.zip").read_bytes()
    assert hashlib.sha256(archive).hexdigest() == read("provenance-integrity.json")["package_sha256"]
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        assert bundle.testzip() is None
        manifest = json.loads(bundle.read("manifest.json"))
        for name, expected in manifest["files"].items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == expected
            assert bundle.read(name) == (HERE / ("packaged-export-" + name)).read_bytes()
    service = EngineeringReports()
    service.session(report["actor"]).reports[value["report_id"]] = raw
    assert service.package(report["actor"], value["report_id"]) == archive
    return read("provenance-integrity.json")


def checks():
    results = {name: pytest(file) for name, file in (("baseline", "baseline-tests.xml"), ("python", "python-release-final.xml"),
               ("focused", "focused-final.xml"), ("native", "native-final.xml"), ("native_p08", "native-p08.xml"))}
    expected = {"baseline": (2736, 76), "python": (2803, 74), "focused": (45, 0), "native": (67, 2), "native_p08": (2, 0)}
    for name, counts in expected.items():
        assert (results[name]["passed"], results[name]["skipped"]) == counts
    stats = read("browser-tests.json")["stats"]
    assert stats["expected"] == 7 and stats["unexpected"] == stats["flaky"] == stats["skipped"] == 0
    measured = read("browser-measurements.json")
    assert measured["pageErrors"] == measured["assetFailures"] == []
    for name in ("accessibility-dark.json", "accessibility-high-contrast.json"):
        entries = read(name)
        assert len(entries) == 5 and all(x["violations"] == [] for x in entries)
    assert all(x["scrollWidth"] <= x["width"] for x in read("responsive.json"))
    rollback = read("rollback-drill.json")
    assert rollback["pass"] and rollback["same_private_root"] and rollback["credentials_unchanged"] and not rollback["destructive_migration"]
    assert read("stress.json")["pass"] and not read("stress.json")["whole_system_peak"]
    native_window = read("native-window-final.json")
    assert native_window["pass"] and native_window["actual_native_renderer"] and not native_window["browser_fallback"]
    assert native_window["backend"] == "webview.platforms.cocoa"
    assert read("physics-parity.json")["pass"] and read("physics_after.json") == read("../P11_2026-10-11/physics_after.json")
    assert read("secret-scan.json")["pass"] and not read("security-review.json")["preview_environment_known_advisories"]
    assert "All checks passed!" in (HERE / "ruff-final.log").read_text()
    assert "Success: no issues found in 351 source files" in (HERE / "mypy-final.log").read_text()
    js = (HERE / "javascript-release.log").read_text()
    assert re.search(r"pass 134\b", js) and re.search(r"fail 0\b", js)
    assert (HERE / "typescript-final.log").read_text() == ""
    assert "No broken requirements found" in (HERE / "pip-check.log").read_text()
    assert (HERE / "build-shell-syntax.log").read_text() == "" and "OK" in (HERE / "package-plist.log").read_text()
    assert read("ci-structure.json")["pass"]
    assert read("github-repository.json")["full_name"] == "COSMOS-PVT-LTD/COSMOS-0.1"
    assert read("github-ci.json")[0]["conclusion"] == "success"
    results.update({"javascript_passed": 134, "browser_passed": 7, "native_window": native_window,
                    "mypy_source_files": 351, "typescript_contract_consumers": 7,
                    "science_exact_http_cases": 5, "candidate_remote_ci_executed": False,
                    "note": "Focused tests overlap full suite; native supplemental counts are not added to a unique grand total"})
    results["commands"] = [
        ".venv-remediation/bin/python -m pytest -q --junitxml=docs/implementation/evidence/P12_2026-10-11/baseline-tests.xml",
        ".venv-release-p12/bin/python -m pytest -q --junitxml=docs/implementation/evidence/P12_2026-10-11/python-release-final.xml",
        ".venv-release-p12/bin/python -m pytest -q tests/unit_tests/infrastructure/test_release_hardening.py tests/integration_tests/gui/test_release_preview_http.py",
        "P07_NATIVE_CONFIG=P12/runtime-config.json COSMOS_P09_NATIVE_CONFIG=P12/runtime-config.json COSMOS_P10_NATIVE=1 .venv-release-p12/bin/python -m pytest -q tests/integration_tests/geometry tests/integration_tests/simulation tests/integration_tests/validation/test_native_comparison.py (expand P12 to absolute phase path)",
        "P08_NATIVE_CONFIG=P12/runtime-config.json .venv-release-p12/bin/python -m pytest -q tests/integration_tests/geometry/test_p08_workbench.py (expand P12 to absolute phase path)",
        "/opt/homebrew/bin/node --test tests/js/*.test.cjs",
        "COSMOS_P12_STATE=<fresh-mktemp-root> COSMOS_P12_APP=<absolute-new-preview-launcher> NODE_PATH=/private/tmp/cosmos-p03.pfPm6s/node_modules /opt/homebrew/bin/node /private/tmp/cosmos-p03.pfPm6s/node_modules/@playwright/test/cli.js test --config tests/ui/release_hardening/playwright.config.cjs",
        ".venv-release-p12/bin/python tests/ui/release_hardening/native_window_smoke.py --url http://127.0.0.1:8842/ --output <new-evidence-output>",
        ".venv-release-p12/bin/python -m ruff check core knowledge physics numerics systems simulation validation api gui infrastructure plugins tests tools",
        ".venv-release-p12/bin/python -m mypy core physics numerics systems api simulation validation knowledge/workspace/evidence_navigation.py infrastructure/release",
        "/opt/homebrew/bin/node /private/tmp/cosmos-p03.pfPm6s/node_modules/typescript/bin/tsc --strict --noEmit --target ES2022 --lib ES2022,DOM --module Node16 --moduleResolution Node16 tests/ui/{design-system,app-shell,ngg,simulation,comparison,knowledge_reports}/type_contracts.ts tests/ui/rocket-workbench/contract-consumer.ts",
        ".venv-release-p12/bin/python -m pip check",
        "pip-audit==2.10.1 --path <preview-site-packages> --strict (separate audit-tools environment)",
    ]
    return results


def write_gate(summary):
    blockers = [
        {"id": "G9-SECURITY-LEGAL", "status": "OPEN", "closure": "Patch and requalify legacy/native-worker advisories including VTK; qualify untrusted Office/XML imports; establish patched interpreter/native/embedded license and security closure; obtain security/legal approval"},
        {"id": "G9-PLATFORM", "status": "OPEN", "closure": "Qualify portable installer/runtime availability, trusted Developer ID signing/notarization, declared platform CI/native journeys and representative whole-system performance/accessibility/migration budgets"},
        {"id": "G9-CI-CHANNEL-SIGNOFF", "status": "OPEN", "closure": "Authorize exact-candidate publication, pass candidate CI, provision/test official private reporting channel, obtain qualified release-owner/platform/security/legal/engineering acceptances"},
    ]
    save("release-signoff.json", {"phase": "P12_RELEASE_HARDENING", "automated_local_preview_checks": "PASS",
                                 "release_owner": "PENDING", "platform_acceptance": "PENDING", "security_acceptance": "PENDING",
                                 "legal_distribution_acceptance": "PENDING", "independent_engineering_acceptance": "PENDING",
                                 "signed_human_approval": False, "official_private_reporting_channel": "NOT_CONFIGURED",
                                 "physical_experiment": "NOT_PERFORMED", "production_handoff": "BLOCKED",
                                 "note": "Automated/source freeze and earlier phase approvals are not release signatures"})
    save("G9_GATE.json", {"gate": "G9 Release", "owner": "Qualified COSMOS release owner (not yet signed)",
                          "phase": "P12_RELEASE_HARDENING", "phase_status": "PARTIAL", "status": "BLOCKED",
                          "local_preview": "PASS", "release_complete": False, "production_handoff": False,
                          "evidence": {"regression": "test-summary.json", "package": "package-integrity.json",
                                       "sbom": "inventory-release-final/sbom.cdx.json", "license_limits": "inventory-release-final/license-gaps.json",
                                       "rollback": "rollback-drill.json", "frozen_registry": "frozen-contract-registry.json",
                                       "security": "security-review.json", "baseline_ci_only": "github-ci.json",
                                       "candidate_preservation": "source-integrity.json", "predecessor": "predecessor-integrity.json",
                                       "documentation": "P12_IMPLEMENTATION_REPORT.md", "signoff": "release-signoff.json"},
                          "blockers": blockers, "physical_acceptance": False, "next": "Close G9 evidence/approval blockers; no automatic release or P13"})


def candidate_files():
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    files = {ROOT / n for n in names if n and (ROOT / n).is_file()}
    files.update(p for p in HERE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    for name in ("dist/P12-release-preview", "dist/P12-release-preview-reproduction"):
        files.update(p for p in (ROOT / name).rglob("*") if p.is_file())
    files.discard(SEAL)
    assert all(p.name != "first-login.json" for p in files)
    return sorted(files)


def main():
    source, prior = preservation()
    summary = checks()
    summary.update({"package": package(), "inventory": inventory(), "provenance": provenance(),
                    "hardware": {"os": "macOS 26.5.2", "cpu": "Apple M1", "architecture": platform.machine(),
                                 "memory_bytes": 8589934592, "cpu_cores": 8, "python": platform.python_version()},
                    "phase_status": "PARTIAL", "G9": "BLOCKED", "production_handoff": False})
    if sys.argv[1:] == ["--verify"]:
        recorded = read("artifact_hashes.json")
        files = candidate_files()
        assert set(recorded) == {str(p.relative_to(ROOT)) for p in files}, "Candidate file set changed"
        for name, expected in recorded.items():
            assert sha(ROOT / name) == expected, name
        assert read("G9_GATE.json")["status"] == "BLOCKED" and read("G9_GATE.json")["release_complete"] is False
        assert read("source-integrity.json") == source and read("predecessor-integrity.json") == prior
        assert read("test-summary.json") == summary
        print(json.dumps({"verify": "PASS", "sealed_files": len(recorded), "G9": "BLOCKED", "phase_status": "PARTIAL"}))
        return
    assert sys.argv[1:] == [] and not SEAL.exists(), "Use --verify on an existing seal"
    save("source-integrity.json", source)
    save("predecessor-integrity.json", prior)
    save("test-summary.json", summary)
    write_gate(summary)
    save("artifact_hashes.json", {str(p.relative_to(ROOT)): sha(p) for p in candidate_files()})
    print(json.dumps({"phase": "P12_RELEASE_HARDENING", "status": "PARTIAL", "G9": "BLOCKED",
                      "python_passed": summary["python"]["passed"], "native_passed": 69, "browser_passed": 7,
                      "sealed_files": len(read("artifact_hashes.json")), "preservation": "PASS"}))


if __name__ == "__main__":
    main()
