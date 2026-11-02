"""Summarize fresh review checks and verify preservation; never restore/edit source.

Only writes verification-summary.json and preservation.json beside this script.
Full and supplemental native test results overlap and are never added together
as independent test counts. Prior P12 evidence remains immutable.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PRIOR = ROOT / "docs/implementation/evidence/P12_2026-10-11"
REVIEW_PREFIX = str(HERE.relative_to(ROOT)) + "/"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode()


def save(name: str, value: Any) -> None:
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def junit(name: str) -> tuple[dict[str, Any], dict[str, str]]:
    path = HERE / name
    root = ET.parse(path).getroot()
    cases = list(root.iter("testcase"))
    states: dict[str, str] = {}
    counts: Counter[str] = Counter()
    skips: Counter[str] = Counter()
    failures = []
    duplicates = []
    for case in cases:
        identifier = str(case.get("classname", "")).lstrip(".") + "::" + str(case.get("name", ""))
        state = "error" if case.find("error") is not None else "failed" if case.find("failure") is not None else "skipped" if case.find("skipped") is not None else "passed"
        if identifier in states:
            duplicates.append(identifier)
        states[identifier] = state
        counts[state] += 1
        if state == "skipped":
            skip = case.find("skipped")
            skips[str(skip.get("message", ""))] += 1
        if state in {"failed", "error"}:
            failures.append(identifier)
    value = {"source": name, "sha256": sha(path), "testcases": len(cases),
             "unique_identifiers": len(states), "passed": counts["passed"],
             "skipped": counts["skipped"], "failed": counts["failed"], "errors": counts["error"],
             "elapsed_testcase_seconds": round(sum(float(c.get("time", "0")) for c in cases), 3),
             "failure_identifiers": failures, "duplicate_identifiers": duplicates,
             "skip_reasons": dict(sorted(skips.items())),
             "status": "PASS" if counts["failed"] == 0 and counts["error"] == 0 and cases else "FAIL"}
    return value, states


def static_evidence(name: str, pattern: str) -> dict[str, Any]:
    path = HERE / name
    value = path.read_text()
    return {"log": name, "sha256": sha(path), "status": "PASS" if re.search(pattern, value) else "UNCONFIRMED",
            "basis": "Recorded fresh command log; not a new command execution by this finalizer"}


def verification() -> dict[str, Any]:
    full, full_ids = junit("python-tests.xml")
    native, native_ids = junit("native-tests.xml")
    p08, p08_ids = junit("native-p08.xml")
    # The later P08 invocation covers the two deliberately flag-skipped cases.
    supplement = dict(native_ids)
    for identifier, state in p08_ids.items():
        if state == "passed" or identifier not in supplement:
            supplement[identifier] = state
    passing = {key for key, state in supplement.items() if state == "passed"}
    overlap = set(supplement) & set(full_ids)
    data = (HERE / "javascript-tests.log").read_text()
    js_counts = {key: int(re.search(r"(?:^|\n)[^\n]*\b" + key + r"\s+(\d+)\s*(?:\n|$)", data).group(1))
                 for key in ("tests", "pass", "fail", "cancelled", "skipped", "todo")}
    typescript = json.loads((HERE / "execution-status.json").read_text())["typescript"]
    ts_paths = typescript.get("consumers", [])
    ts = {**typescript, "status": "PASS" if typescript.get("exit_code") == 0 and len(ts_paths) == 7
          and all((ROOT / path).is_file() for path in ts_paths) else "UNCONFIRMED",
          "consumers_count": len(ts_paths), "execution_evidence": "execution-status.json",
          "execution_evidence_sha256": sha(HERE / "execution-status.json"),
          "log_sha256": sha(HERE / typescript["log"]),
          "basis": "Coordinator-observed exit code and exact command; empty success log alone is not used as proof"}
    mypy = static_evidence("mypy.log", r"Success: no issues found in 351 source files")
    mypy["scope"] = "Existing explicitly selected packages; not whole-repository/GUI typing"
    mypy["source_files"] = 351
    return {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "Fresh local review checks, not release/engineering/physical acceptance",
            "python_full_suite": full, "native_supplemental": native, "native_p08_flag_specific": p08,
            "native_overlap_accounting": {"raw_supplemental_testcase_rows": native["testcases"] + p08["testcases"],
                "unique_supplemental_identifiers": len(supplement), "unique_supplemental_passed": len(passing),
                "repeated_between_native_and_p08": len(set(native_ids) & set(p08_ids)),
                "overlapping_with_full_suite": len(overlap),
                "supplemental_not_in_full_suite": sorted(set(supplement) - set(full_ids)),
                "full_suite_skips_exercised_as_native_passes": len({key for key in passing if full_ids.get(key) == "skipped"}),
                "note": "Do not add supplemental native passes to full-suite passes as independent/unique tests. Counts above identify overlap and optional backend coverage."},
            "javascript": {"log": "javascript-tests.log", "sha256": sha(HERE / "javascript-tests.log"),
                **js_counts, "status": "PASS" if js_counts["fail"] == 0 and js_counts["cancelled"] == 0 and js_counts["pass"] > 0 else "FAIL"},
            "ruff": static_evidence("ruff.log", r"All checks passed!"), "mypy": mypy, "typescript": ts,
            "pip_consistency": static_evidence("pip-check.log", r"No broken requirements found\."),
            "not_covered_by_green_tests": ["Production release or physical readiness", "Security role-spoof/legacy mutation defects reproduced separately",
                "Unqualified platforms/standalone installation/signing", "Missing experimental data and human acceptance"],
            "security_diagnostic": {"source": "security-boundary-probe.json", "sha256": sha(HERE / "security-boundary-probe.json"),
                "assertion": "Reproduced existing defects; successful reproduction is not a security PASS"}}


def compare(expected: dict[str, str]) -> dict[str, Any]:
    changed = []
    missing = []
    exclusions = []
    matched = 0
    for name, expected_sha in sorted(expected.items()):
        if name.startswith(REVIEW_PREFIX):
            exclusions.append(name)
            continue
        path = ROOT / name
        if not path.is_file():
            missing.append(name)
            continue
        actual = sha(path)
        if actual != expected_sha:
            changed.append({"path": name, "expected_sha256": expected_sha, "actual_sha256": actual,
                            "actual_bytes": path.stat().st_size})
        else:
            matched += 1
    return {"declared_files": len(expected), "checked_files": len(expected) - len(exclusions),
            "matched_files": matched, "changed": changed, "missing": missing, "excluded_review_files": exclusions,
            "status": "PASS" if not changed and not missing else "MISMATCH"}


def preservation() -> dict[str, Any]:
    baseline = json.loads((HERE / "baseline.json").read_text())
    sealed = json.loads((PRIOR / "artifact_hashes.json").read_text())
    previous = compare(sealed)
    original = compare(baseline["sha256"])
    current_names = {name for name in git("ls-files", "-co", "--exclude-standard", "-z").split("\0")
                     if name and not name.startswith(REVIEW_PREFIX) and (ROOT / name).is_file()}
    added = sorted(current_names - set(baseline["sha256"]))
    cache = ROOT / "cache/cea/test_key.json"
    before = HERE / "cea-cache-before.json"
    cache_record = {"path": "cache/cea/test_key.json", "before_copy": "cea-cache-before.json",
                    "before_sha256": sha(before), "current_sha256": sha(cache),
                    "before_bytes": before.stat().st_size, "current_bytes": cache.stat().st_size,
                    "exact_bytes_match": before.read_bytes() == cache.read_bytes(),
                    "known_test_generated_fixture": True, "restored_by_this_finalizer": False}
    old_json, new_json = json.loads(before.read_bytes()), json.loads(cache.read_bytes())
    cache_record["changed_top_level_fields"] = sorted(key for key in set(old_json) | set(new_json) if old_json.get(key) != new_json.get(key))
    for key in ("created_at", "expires_at"):
        if old_json.get(key) != new_json.get(key):
            cache_record[key] = {"before": old_json.get(key), "current": new_json.get(key)}
    current_head = git("rev-parse", "HEAD").strip()
    seal_sha = sha(PRIOR / "artifact_hashes.json")
    status = ("PASS" if previous["status"] == "PASS" and original["status"] == "PASS" and not added
              and current_head == baseline["head"] and seal_sha == baseline["P12_seal_sha256"]
              and len(sealed) == 5047 else "MISMATCH")
    return {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "status": status,
            "current_head": current_head, "baseline_head": baseline["head"], "head_unchanged": current_head == baseline["head"],
            "prior_P12_seal": {"path": str((PRIOR / "artifact_hashes.json").relative_to(ROOT)), "sha256": seal_sha,
                "baseline_recorded_sha256": baseline["P12_seal_sha256"], "seal_bytes_unchanged": seal_sha == baseline["P12_seal_sha256"],
                "expected_entry_count": 5047, "entry_count_matches": len(sealed) == 5047, **previous},
            "review_original_files": {"baseline": "baseline.json", "baseline_sha256": sha(HERE / "baseline.json"), **original},
            "added_outside_review": added,
            "added_scan_basis": "Same Git tracked/nonignored-untracked inventory command as review baseline; not a scan of entire ignored virtual environments, OS or unrelated user directories",
            "known_cache_fixture": cache_record,
            "review_directory_excluded": REVIEW_PREFIX,
            "nonmutation": {"prior_seal_rewritten": False, "production_changed": False, "cache_restored": False,
                            "only_outputs": ["verification-summary.json", "preservation.json"]}}


def main() -> None:
    tests = verification()
    files = preservation()
    save("verification-summary.json", tests)
    save("preservation.json", files)
    print(json.dumps({"python": {key: tests["python_full_suite"][key] for key in ("passed", "skipped", "failed", "errors")},
                      "native_unique_supplemental_passes": tests["native_overlap_accounting"]["unique_supplemental_passed"],
                      "native_overlap_full_suite": tests["native_overlap_accounting"]["overlapping_with_full_suite"],
                      "javascript_passes": tests["javascript"]["pass"], "static": {key: tests[key]["status"] for key in ("ruff", "mypy", "typescript", "pip_consistency")},
                      "preservation": files["status"], "prior_sealed": files["prior_P12_seal"]["checked_files"],
                      "prior_changed": [x["path"] for x in files["prior_P12_seal"]["changed"]],
                      "original_changed": [x["path"] for x in files["review_original_files"]["changed"]],
                      "added_outside_review": files["added_outside_review"]}, sort_keys=True))


if __name__ == "__main__":
    main()
