"""Capture a read-only source baseline and predecessor seal before P10 edits."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def main():
    target = HERE / "baseline.json"
    assert not target.exists(), "Do not replace the baseline"
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
              for name in sorted(set(names)) if name and (ROOT / name).is_file()}
    before = HERE / "before"
    for name in ("gui/server.py", ".github/workflows/ci.yml"):
        out = before / name
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("xb") as stream:
            stream.write((ROOT / name).read_bytes())
    target.write_text(json.dumps({"commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        "status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT).decode(), "sha256": hashes}, indent=2) + "\n")
    print(json.dumps({"baseline_files": len(hashes), "predecessor_verified": 2988}))


if __name__ == "__main__":
    main()
