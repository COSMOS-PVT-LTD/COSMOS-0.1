"""Capture and compare existing repository content, excluding this P02 evidence."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def inventory():
    paths = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    ).decode().split("\0")
    return {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in sorted(set(paths))
        if name and (ROOT / name).is_file()
        and not name.startswith("docs/implementation/evidence/P02_2026-10-08/")
    }


if __name__ == "__main__":
    current = inventory()
    baseline = HERE / "source_before.json"
    if sys.argv[1:] == ["capture"]:
        if baseline.exists():
            raise SystemExit("Refusing to replace existing checkpoint")
        baseline.write_text(json.dumps(current, indent=2) + "\n")
        print(f"Captured {len(current)} pre-existing files")
    else:
        before = json.loads(baseline.read_text())
        changed = [p for p, digest in before.items() if current.get(p) != digest]
        added = sorted(set(current) - set(before))
        result = {"preexisting_files": len(before), "changed_or_missing": changed,
                  "added_outside_p02": added, "pass": not changed and not added}
        (HERE / "source_integrity.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))
        raise SystemExit(0 if result["pass"] else 1)
