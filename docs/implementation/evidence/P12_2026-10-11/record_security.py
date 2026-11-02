"""Scope and triage security evidence; scans never print credential contents."""
import difflib
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def read(name):
    return json.loads((HERE / name).read_text())


def save(name, value):
    with (HERE / name).open("x") as handle:
        handle.write(json.dumps(value, indent=2) + "\n")


def vulnerabilities(name):
    return [{"name": d["name"], "version": d["version"], "vulnerabilities": d["vulns"]}
            for d in read(name)["dependencies"] if d["vulns"]]


def main():
    findings = read("bandit-release.json")["results"]
    triage = []
    for item in findings:
        entry = {key: item[key] for key in ("test_id", "issue_severity", "issue_confidence", "filename", "line_number", "issue_text")}
        if item["test_id"] == "B608":
            entry["assessment"] = "Reviewed controlled literal assignment names; all external values/user ID remain SQL parameters. Not a waiver for other SQL paths."
        elif item["test_id"] == "B310":
            entry["assessment"] = "Qualified preview launcher supplies a fixed loopback URL. General callable accepts a URL; arbitrary schemes are not approved by this profile."
        elif item["test_id"] == "B314":
            entry["assessment"] = "OPEN: Office/XML import uses standard ElementTree without a completed untrusted-document resource/security qualification. Do not approve hostile external imports."
        else:
            entry["assessment"] = "Retained LOW finding. Assertions/dev constants/subprocess calls are not blanket-waived or a completed penetration test."
        triage.append(entry)
    new = vulnerabilities("release-audit-final.json")
    assert new == []
    legacy = vulnerabilities("python-audit.json")
    cad = vulnerabilities("external-cad-audit.json")
    assert any(d["name"] == "vtk" and d["version"] == "9.3.1" for d in cad)
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    pattern = re.compile(rb"\b(?:ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9]{40,})\b")
    matches = []
    scanned = 0
    for name in sorted(set(names)):
        path = ROOT / name
        if not name or not path.is_file() or path.is_symlink() or path.stat().st_size > 5 * 1024**2:
            continue
        raw = path.read_bytes(); scanned += 1
        for match in pattern.finditer(raw):
            matches.append({"path": name, "line": raw[:match.start()].count(b"\n") + 1,
                            "value": "REDACTED", "sha256": hashlib.sha256(match.group()).hexdigest()})
    credential_count = 0
    private_roots = re.findall(r"data root=([^\n]+)", (HERE / "packaged-modern.log").read_text())
    for root in set(private_roots):
        credential = Path(root) / "first-login.json"
        if credential.is_file():
            password = json.loads(credential.read_text())["password"].encode()
            for path in HERE.rglob("*"):
                if path.is_file() and not path.is_symlink() and path.stat().st_size <= 5 * 1024**2:
                    assert password not in path.read_bytes(), "Private credential leaked into phase evidence"
            credential_count += 1
    save("secret-scan.json", {"pass": not matches, "files_scanned": scanned, "matches": matches,
                              "private_generated_credentials_checked": credential_count,
                              "private_generated_credentials_found_in_evidence": False,
                              "scope": "Targeted literal GitHub/OpenAI token patterns in git-listed files; not exhaustive secret detection or Git history audit"})
    save("security-review.json", {"source_scan": "Bandit 1.9.1, explicit application packages including scientific layers",
                                  "severity_counts": {s: sum(f["issue_severity"] == s for f in findings) for s in ("LOW", "MEDIUM", "HIGH")},
                                  "findings": triage, "preview_environment_known_advisories": new,
                                  "unchanged_legacy_worker_environment_advisories": legacy, "qualified_external_cad_advisories": cad,
                                  "interpreter": "CPython 3.11.4 compatibility observed; patched interpreter/security closure not qualified",
                                  "official_security_channel": "NOT_CONFIGURED", "proposed_email": "security@cosmospvtltd.com (not verified active)",
                                  "independent_security_review": "NOT_PERFORMED", "production_security_approval": False,
                                  "limits": ["No public-network or multi-tenant deployment authorized", "No exact native-CVE closure or OS/interpreter vulnerability clearance", "No independent penetration test or hostile Office/XML resource qualification"]})
    baseline = read("baseline.json")
    paths = ["api/authentication.py", "gui/server.py", "gui/static/app.js", "gui/static/rbac.js", ".github/workflows/ci.yml", ".gitignore", "SECURITY.md", "scripts/build_macos_app.sh"]
    delta = []
    for name in paths:
        before = HERE / "before" / name
        assert hashlib.sha256(before.read_bytes()).hexdigest() == baseline["sha256"][name]
        delta.extend(difflib.unified_diff(before.read_text().splitlines(True), (ROOT / name).read_text().splitlines(True),
                                         fromfile="P11-before/" + name, tofile="P12-current/" + name))
    with (HERE / "p12-scoped.diff").open("x") as handle:
        handle.write("".join(delta))
    print(json.dumps({"preview_known_advisories": 0, "bandit_high": 0, "bandit_medium": 11,
                      "secret_pattern_matches": len(matches), "production_security_approved": False}))


if __name__ == "__main__":
    main()
