"""Seal or verify local P04 evidence; never publish, mutate stores or accept gaps."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SHA = "293223ebef190eaa647e67dc581eb186b2b5d987"
LOGS = (
    "pytest-final.log",
    "pytest-final.xml",
    "python-focused-final.log",
    "scientific-flag-on.log",
    "js-full-final.log",
    "browser-final.log",
    "legacy-visual-regression.log",
    "component-visual-regression.log",
    "ruff-final.log",
    "mypy-final.log",
    "typecheck-final.log",
    "p03-retained-evidence.log",
)


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def scope() -> dict:
    subprocess.run(
        [sys.executable, str(HERE / "check_scope.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    result = json.loads((HERE / "source_integrity.json").read_text())
    assert result["pass"] and not result["scientificSourceChanged"]
    return result


def require_log(name: str, pattern: str) -> None:
    assert re.search(pattern, (HERE / "logs" / name).read_text()), name


def build(output: Path) -> None:
    assert (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
        == SHA
    )
    (HERE / "logs").mkdir(exist_ok=True)
    for name in LOGS:
        shutil.copy2(output / name, HERE / "logs" / name)
    integrity = scope()
    suites = list(ET.parse(HERE / "logs/pytest-final.xml").getroot().iter("testsuite"))
    counts = {
        key: sum(int(s.get(key, "0")) for s in suites)
        for key in ("tests", "errors", "failures", "skipped")
    }
    assert counts == {"tests": 2270, "errors": 0, "failures": 0, "skipped": 5}, counts
    require_log("python-focused-final.log", r"31 passed")
    require_log("scientific-flag-on.log", r"3 passed")
    require_log("js-full-final.log", r"pass 84")
    require_log("js-full-final.log", r"fail 0")
    require_log("browser-final.log", r"26 passed")
    require_log("legacy-visual-regression.log", r"12 passed")
    require_log("component-visual-regression.log", r"19 passed")
    require_log("ruff-final.log", r"All checks passed!")
    require_log("mypy-final.log", r"Success: no issues found in 318 source files")
    require_log("p03-retained-evidence.log", r'"evidenceHashes": "PASS"')
    assert not (HERE / "logs/typecheck-final.log").read_text().strip()
    browser = json.loads((HERE / "browser-tests.json").read_text())["stats"]
    assert (
        browser["expected"] == 26
        and browser["unexpected"] == browser["flaky"] == browser["skipped"] == 0
    )
    accessibility = {}
    for theme in ("dark", "high-contrast"):
        result = json.loads((HERE / f"accessibility-{theme}.json").read_text())
        assert not result["violations"]
        review = json.loads((HERE / "accessibility-contrast-review.json").read_text())[
            theme
        ]
        reviewed = {tuple(item["target"]): item for item in review["measurements"]}
        for rule in result["incomplete"]:
            assert rule["id"] == "color-contrast"
            for node in rule["nodes"]:
                measurement = reviewed[tuple(node["target"])]
                assert measurement["visible"] and measurement["contrast"] >= 4.5
        accessibility[theme] = {
            "violations": 0,
            "incomplete_rules_retained": len(result["incomplete"]),
            "supplementary_contrast_review": "PASS",
            "rulesPassed": len(result["passes"]),
        }
    metrics = json.loads((HERE / "interaction-metrics.json").read_text())
    assert metrics["samples"] == 50 and metrics["plotMutations"] == 0
    routes = json.loads((HERE / "route-compatibility.json").read_text())
    assert len(routes) == len({r["workbenchId"] for r in routes}) == 12
    assert all(r["http"] == 200 for r in routes)
    fixture = ROOT / "cache/cea/test_key.json"
    assert (
        hashlib.sha256(fixture.read_bytes()).hexdigest()
        == "6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508"
    )
    subprocess.run(
        ["git", "diff", "--check"], cwd=ROOT, check=True, capture_output=True
    )
    chrome_info = Path("/Applications/Google Chrome.app/Contents/Info.plist")
    with chrome_info.open("rb") as source:
        chrome = plistlib.load(source)["CFBundleShortVersionString"]
    tools = json.loads(
        (
            ROOT
            / "docs/implementation/evidence/P03_2026-10-08/tooling/package-lock.json"
        ).read_text()
    )
    versions = {
        name: tools["packages"]["node_modules/" + name]["version"]
        for name in ("@playwright/test", "axe-core", "typescript")
    }
    gate = {
        "gate_id": "G3",
        "phase": "P04_APP_SHELL",
        "owner_role": "Integration lead",
        "reviewer": "Codex integration lead; executed local software evidence",
        "decision": "PASS_TESTED_DEFAULT_OFF_INTEGRATION_SLICE",
        "status": "PASS",
        "authorization": "User requested continue with P04; no new architecture authority inferred",
        "base_commit_sha": SHA,
        "dirty_checkout": True,
        "date_local": "2026-10-09",
        "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "node": subprocess.check_output(["node", "--version"]).decode().strip(),
            "chrome": chrome,
            "test_tools": versions,
        },
        "tests": {
            "python_passed": 2265,
            "python_skipped": 5,
            "focused_p04_python": 31,
            "javascript": 84,
            "p04_browser": 26,
            "legacy_screenshots": 12,
            "component_screenshots": 19,
            "existing_propulsion_http_flag_on": 3,
            "ruff": "PASS",
            "mypy_files": 318,
            "typescript_public_contracts": "PASS",
            "accessibility_new_scope": accessibility,
            "retained_p03_evidence": "PASS",
        },
        "preservation": {
            "checkpoint_files": integrity["preexistingFiles"],
            "allowed_existing_changes": integrity["allowedProductionChanges"],
            "unexpected": [],
            "scientific_source_changed": False,
            "cache_fixture_exactly_restored": True,
        },
        "rollback": {
            "server_default": "OFF",
            "opt_in": "COSMOS_NEW_SHELL=1",
            "route_override": "shell=legacy",
            "in_place_original_DOM_and_draft_retained": True,
        },
        "boundaries": [
            "UI Project preference is not authoritative Project storage",
            "History is change-event inspection, not immutable historical snapshot restoration",
            "Existing mutable-store CAS race remains a later persistence gate",
            "Knowledge queue only; physics/native jobs and cancellation unavailable",
            "No native production approval, full legacy redesign, remote CI or hardware validation",
        ],
        "architecture_changed": False,
        "scientific_backend_activated": False,
        "user_server_restarted": False,
        "committed": False,
        "pushed": False,
        "p05_readiness": "READY_FOR_P05_UI_SCOPE_ON_USER_REQUEST",
        "p05_started": False,
    }
    write(HERE / "G3_GATE.json", gate)
    files = [
        p
        for p in HERE.rglob("*")
        if p.is_file()
        and p.name != "artifact_hashes.json"
        and "__pycache__" not in p.parts
    ]
    files += [p for p in (ROOT / "gui/static/app-shell").rglob("*") if p.is_file()]
    files += [
        p
        for p in (ROOT / "tests/ui/app-shell").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    ]
    files += [
        ROOT / "gui/app_shell.py",
        ROOT / "tests/js/app_shell.test.cjs",
        ROOT / "tests/unit_tests/gui/test_app_shell.py",
        ROOT / "tests/integration_tests/gui/test_app_shell_http.py",
    ]
    files += [ROOT / name for name in integrity["allowedProductionChanges"]]
    write(
        HERE / "artifact_hashes.json",
        {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(files))
        },
    )
    verify()


def verify() -> None:
    scope()
    gate = json.loads((HERE / "G3_GATE.json").read_text())
    assert gate["status"] == "PASS" and not gate["scientific_backend_activated"]
    entries = json.loads((HERE / "artifact_hashes.json").read_text())
    for name, expected in entries.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    print(
        json.dumps(
            {
                "gate": "G3",
                "status": "PASS",
                "artifact_hashes": "PASS",
                "artifacts": len(entries),
                "python": 2265,
                "javascript": 84,
                "p04_browser": 26,
                "baseline_screenshots": 31,
                "unexpected_source_changes": 0,
                "rollout": "default-off",
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        verify()
    else:
        assert args.output and args.output.is_dir(), (
            "Supply the temporary P04 output directory"
        )
        build(args.output)
