"""Prepare isolated audit evidence; do not alter production or prior evidence."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
prior = ROOT / "docs/implementation/evidence/P12_2026-10-11"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as handle:
        handle.write(json.dumps(value, indent=2) + "\n")


def main():
    sealed = json.loads((prior / "artifact_hashes.json").read_text())
    assert len(sealed) == 5047
    for name, expected in sealed.items():
        assert sha(ROOT / name) == expected, name
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    original = {n: sha(ROOT / n) for n in sorted(set(names)) if n and (ROOT / n).is_file() and not (ROOT / n).is_relative_to(HERE)}
    save(HERE / "baseline.json", {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
                                   "status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT).decode(),
                                   "sha256": original, "P12_seal_verified_files": len(sealed), "P12_seal_sha256": sha(prior / "artifact_hashes.json")})
    with (HERE / "cea-cache-before.json").open("xb") as handle:
        handle.write((ROOT / "cache/cea/test_key.json").read_bytes())
    runtime = json.loads((prior / "runtime-config.json").read_text())
    runtime["evidence_directory"] = str(HERE / "native-evidence")
    save(HERE / "runtime-config.json", runtime)
    data = Path(tempfile.mkdtemp(prefix="cosmos-complete-review-"))
    save(HERE / "session.json", {"data_root": str(data), "port": 8843, "url": "http://127.0.0.1:8843/",
                                 "profile": "local-preview", "runtime_config": str(HERE / "runtime-config.json"),
                                 "purpose": "Fresh audit screenshots/diagnostics; isolated from user and prior phase data"})
    print(json.dumps({"baseline_files": len(original), "P12_seal": "PASS", "isolated_root": str(data)}))


if __name__ == "__main__":
    main()
