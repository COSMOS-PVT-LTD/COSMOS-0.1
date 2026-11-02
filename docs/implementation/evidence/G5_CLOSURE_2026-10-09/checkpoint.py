import hashlib
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREFIX = str(HERE.relative_to(ROOT)) + "/"
names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
entries = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(set(names))
           if name and (ROOT / name).is_file() and not name.startswith(PREFIX)}
assert not (HERE / "source_before.json").exists()
(HERE / "source_before.json").write_text(json.dumps(entries, indent=2) + "\n")
old = json.loads((HERE.parent / "P07_2026-10-09/artifact_hashes.json").read_text())
for name, sha in old.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha
    if not name.startswith("docs/"):
        target = HERE / "before" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
print(json.dumps({"checkpointFiles": len(entries), "originalP07Seal": "PASS", "historicalSourceArchived": True}))
