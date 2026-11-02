"""Retain original working-tree bytes and hashes; never reset user changes."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
assert not (OUT / "baseline.json").exists(), "Do not replace the preserved pre-P09 working-tree checkpoint"
paths = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths
          if name and (ROOT / name).is_file() and not name.startswith("docs/implementation/evidence/P09_2026-10-10/")}
(OUT / "baseline.json").write_text(json.dumps({"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
    "status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT).decode(), "sha256": hashes}, indent=2) + "\n")
for name in ("gui/server.py", ".github/workflows/ci.yml"):
    target = OUT / "before" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((ROOT / name).read_bytes())
print(json.dumps({"baseline_files": len(hashes), "retained_originals": 2}))
