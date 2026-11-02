"""Preserve the verified dirty-tree baseline; never replace predecessor gates."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def main():
    assert not (HERE / "baseline.json").exists()
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    hashes = {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(set(names)) if n and (ROOT/n).is_file()}
    for name in ("gui/server.py", ".github/workflows/ci.yml", "cache/cea/test_key.json"):
        target = HERE / "before" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output:
            output.write((ROOT/name).read_bytes())
    (HERE/"baseline.json").write_text(json.dumps({"commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(), "sha256": hashes,
        "predecessor_sealed_files": 3116}, indent=2)+"\n")
    print(json.dumps({"baseline_files": len(hashes), "predecessor_verified": 3116}))


if __name__ == "__main__":
    main()
