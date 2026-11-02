"""Pin the dirty P11 handoff before P12; preserve planned edits and local app."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = HERE / "baseline.json"
    assert not target.exists()
    predecessor = json.loads((HERE.parent / "P11_2026-10-11/artifact_hashes.json").read_text())
    assert len(predecessor) == 3202
    for name, expected in predecessor.items():
        assert sha(ROOT / name) == expected, name
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    hashes = {n: sha(ROOT / n) for n in sorted(set(names)) if n and (ROOT / n).is_file()}
    for name in ("gui/server.py", "api/authentication.py", ".github/workflows/ci.yml", "scripts/build_macos_app.sh",
                 "SECURITY.md", "requirements-dev.txt", "requirements-desktop.txt", "requirements-cea.txt",
                 "requirements-numerics.txt", "cache/cea/test_key.json"):
        out = HERE / "before" / name
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("xb") as handle:
            handle.write((ROOT / name).read_bytes())
    old_app = ROOT / "dist/COSMOS 0.1.app"
    app = {str(p.relative_to(old_app)): sha(p) for p in old_app.rglob("*") if p.is_file()}
    with target.open("x") as handle:
        json.dump({"commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
                   "sha256": hashes, "predecessor_sealed_files": len(predecessor), "existing_mac_app": app}, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"baseline_files": len(hashes), "P11_verified": len(predecessor), "existing_app_files": len(app)}))


if __name__ == "__main__":
    main()
