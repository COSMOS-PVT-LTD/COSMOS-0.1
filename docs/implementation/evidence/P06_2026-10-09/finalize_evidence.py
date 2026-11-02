"""Seal P06 software evidence. --verify is read-only and does not rerun tests."""
import hashlib
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
P05 = HERE.parent / "P05_2026-10-09"
LOGS = ("focused-final.log", "focused-final.xml", "pytest-final.log", "pytest-final.xml",
        "js-final.log", "ruff-final.log", "mypy-final.log", "physics-parity.log", "benchmark.log",
        "p02-preflight.log", "p05-preflight.log", "schema-install.log", "schema-lock-verification.log",
        "focused-initial.log", "focused-initial.xml", "mypy-initial.log", "ruff-initial.log", "ruff-fixes.log")
EXPECTED_COMMIT = "293223ebef190eaa647e67dc581eb186b2b5d987"


def read(name):
    return json.loads((HERE / name).read_text())


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scope():
    spec = importlib.util.spec_from_file_location("p06_scope", HERE / "check_scope.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    before, current = read("source_before.json"), module.hashes()
    changes = [name for name, sha in before.items() if current.get(name) != sha]
    additions = sorted(name for name in current if name not in before)
    assert len(before) == 1808 and not changes, changes
    assert all(name.startswith(module.ADDITIONS) for name in additions), additions
    assert digest(ROOT / "cache/cea/test_key.json") == "6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508"
    return additions


def predecessor():
    entries = json.loads((P05 / "artifact_hashes.json").read_text())
    assert len(entries) == 71
    for name, sha in entries.items():
        assert digest(ROOT / name) == sha, name
    gate = json.loads((P05 / "G4_GATE.json").read_text())
    assert gate["status"] == "PASS" and not gate["scientific_source_changed"] and gate["default_off"]
    return {"gate": "G4", "status": "PASS_RETAINED", "sealed_entries": len(entries),
            "artifact_manifest_sha256": digest(P05 / "artifact_hashes.json"),
            "prior_source_and_evidence_changed": False,
            "note": "P05 strict scope is historical; its verifier ran before P06. Retained seals checked read-only after additive P06 work."}


def suite(name, expected_tests, expected_skips):
    element = ET.parse(HERE / "logs" / name).getroot().find("testsuite")
    assert element is not None
    attributes = element.attrib
    assert int(attributes["tests"]) == expected_tests
    assert int(attributes["skipped"]) == expected_skips
    assert int(attributes["failures"]) == int(attributes["errors"]) == 0
    return {"passed": expected_tests - expected_skips, "skipped": expected_skips,
            "failures": 0, "errors": 0, "seconds": float(attributes["time"])}


def check():
    additions = scope()
    previous = predecessor()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip() == EXPECTED_COMMIT
    tests = {"focused": suite("focused-final.xml", 204, 0), "python": suite("pytest-final.xml", 2481, 5)}
    for name, fragments in {"js-final.log": ["pass 94", "fail 0"], "ruff-final.log": ["All checks passed"],
                            "mypy-final.log": ["Success: no issues found in 325 source files"],
                            "schema-lock-verification.log": ["Would install", "jsonschema-4.25.1"]}.items():
        text = (HERE / "logs" / name).read_text()
        assert all(fragment in text for fragment in fragments), name
    parity = read("physics_parity.json")
    assert parity["pass"] and parity["actualHTTPcases"] == 5 and parity["numericalTolerance"] == 0
    assert parity["baselineSHA256"] == digest(P05 / "physics_before.json")
    assert read("physics_after.json") == json.loads((P05 / "physics_before.json").read_text())
    schema = json.loads((ROOT / "systems/contracts/geometry/schemas/geometry-v1.schema.json").read_text())
    assert len(schema["$defs"]) == 13
    vectors = json.loads((ROOT / "tests/contracts/geometry/golden-v1.json").read_text())
    assert vectors["synthetic_only"] and len(vectors["vectors"]) == 14
    costs = read("contract_costs.json")
    assert costs["feature_count"] == 512 and costs["frame_count"] == 64 and costs["parameter_count"] == 256
    assert costs["synthetic_only"] and not costs["native_kernel_invoked"] and not costs["timing_gate_claimed"]
    installed = read("schema-install.json")["install"]
    resolved = read("schema-lock-verification.json")["install"]
    def closure(items):
        return {i["metadata"]["name"]: (i["metadata"]["version"], i["download_info"]["archive_info"]["hashes"]["sha256"]) for i in items}
    assert len(installed) == 6 and closure(installed) == closure(resolved)
    return additions, previous, tests


def build(output):
    (HERE / "logs").mkdir(exist_ok=True)
    for name in LOGS:
        shutil.copy2(output / name, HERE / "logs" / name)
    for name in ("schema-install.json", "schema-lock-verification.json"):
        shutil.copy2(output / name, HERE / name)
    subprocess.run([sys.executable, str(HERE / "check_scope.py")], cwd=ROOT, check=True, capture_output=True)
    additions, previous, tests = check()
    write("predecessor_integrity.json", previous)
    environment = {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
                   "architecture": platform.machine(), "macos": platform.mac_ver()[0],
                   "pytest": version("pytest"), "ruff": version("ruff"), "mypy": version("mypy"),
                   "node": subprocess.check_output(["node", "--version"]).decode().strip(),
                   "schema_tooling": [{"name": i["metadata"]["name"], "version": i["metadata"]["version"],
                                       "wheel_sha256": i["download_info"]["archive_info"]["hashes"]["sha256"]}
                                      for i in read("schema-install.json")["install"]]}
    write("P06_CONTRACT_DECISION.json", {
        "gate_id": "P06_CONTRACTS_PRE_G5", "phase": "P06_NGG_CONTRACTS", "status": "PASS",
        "requirement_ids": ["NGG-001", "NGG-002", "NGG-003", "NGG-004", "NGG-006",
                            "P06 required schemas/serialization/dependency tests", "specs/04 contract/state metadata"],
        "requirement_scope": "Contracts only. NGG-005 actual QA and NGG-007 actual reimport remain deferred to P07/G5.",
        "commit_sha": EXPECTED_COMMIT, "dirty_checkout": True, "environment": environment,
        "commands": {
            "focused": "PYTHONPATH=<temporary schema-tools> .venv-remediation/bin/python -m pytest -q tests/unit_tests/systems_layer/test_geometry_*.py tests/contracts/geometry --junitxml=<output>/focused-final.xml",
            "python": "PYTHONPATH=<temporary schema-tools> .venv-remediation/bin/python -m pytest -q --junitxml=<output>/pytest-final.xml",
            "javascript": "node --test tests/js/*.test.cjs",
            "ruff": ".venv-remediation/bin/python -m ruff check core knowledge physics numerics systems api gui infrastructure plugins tests tools",
            "mypy": ".venv-remediation/bin/python -m mypy core physics numerics systems api",
            "physics": ".venv-remediation/bin/python docs/implementation/evidence/P06_2026-10-09/verify_physics.py",
            "benchmark": "PYTHONPATH=. .venv-remediation/bin/python docs/implementation/evidence/P06_2026-10-09/benchmark_contracts.py",
            "scope": ".venv-remediation/bin/python docs/implementation/evidence/P06_2026-10-09/check_scope.py",
            "schema_lock": ".venv-remediation/bin/python -m pip install --dry-run --ignore-installed --target <temporary pin-check> --require-hashes --only-binary=:all: -r docs/implementation/evidence/P06_2026-10-09/requirements-schema-tests.txt --report <output>/schema-lock-verification.json",
        },
        "tests": {**tests, "javascript_passed": 94, "ruff": "PASS", "mypy_sources": 325,
                  "independent_schema_validation": "PASS_EXECUTED_NOT_SKIPPED", "wire_definitions": 13, "golden_vectors": 14,
                  "scientific_http_cases": 5, "scientific_comparison": "exact", "scientific_tolerance": 0},
        "test_artifacts": ["logs/focused-final.xml", "logs/pytest-final.xml", "logs/js-final.log", "physics_parity.json",
                           "source_integrity.json", "predecessor_integrity.json", "contract_costs.json", "artifact_hashes.json"],
        "reviewer": "Codex local software/contract review; not independent CAD, physics or release approval",
        "decision": "PASS_DORMANT_TYPED_CONTRACT_SLICE_P07_READY", "date": datetime.now(timezone.utc).isoformat(),
        "blockers": [], "existing_files_changed": [], "baseline_file_count": 1808, "added_contract_test_files": additions,
        "native_geometry_activated": False, "new_runtime_dependency": False, "new_storage_authority": False,
        "physical_validation_claimed": False, "publishing_performed": False, "G5_passed": False,
        "gui_browser_rerun": "NOT_RUN_P06; unchanged GUI/P05 52-case historical evidence sealed and retained",
        "release_ci_rerun": "NOT_RUN; no commit/push requested", "next": "P07_NGG_KERNELS; not started"})
    files = [p for p in HERE.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name != "artifact_hashes.json"]
    files += [ROOT / name for name in additions]
    files.append(P05 / "artifact_hashes.json")
    write("artifact_hashes.json", {str(p.relative_to(ROOT)): digest(p) for p in sorted(set(files))})


def verify():
    for name, sha in read("artifact_hashes.json").items():
        assert digest(ROOT / name) == sha, name
    _, _, tests = check()
    decision = read("P06_CONTRACT_DECISION.json")
    assert decision["status"] == "PASS" and not decision["G5_passed"] and not decision["native_geometry_activated"]
    print(json.dumps({"status": "PASS", "phase": "P06_NGG_CONTRACTS", "sealed_entries": len(read("artifact_hashes.json")),
                      "python_passed": tests["python"]["passed"], "focused_passed": tests["focused"]["passed"],
                      "existing_changes": 0, "G5_passed": False, "next": "P07_NGG_KERNELS; not started"}))


if __name__ == "__main__":
    if sys.argv[1:] != ["--verify"]:
        assert len(sys.argv) == 2, "Provide the executed output directory or --verify"
        build(Path(sys.argv[1]))
    verify()
