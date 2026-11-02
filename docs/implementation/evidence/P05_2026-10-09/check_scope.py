"""P05 checkpoint protects pre-existing work and all predecessor evidence."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREFIX = str(HERE.relative_to(ROOT)) + "/"
ALLOWED = {"gui/app_shell.py", "gui/server.py", "gui/static/app-shell/shell.js",
           "gui/static/propulsion-suite.js"}
ADDITIONS = (PREFIX, "gui/static/rocket-workbench/", "tests/js/rocket_workbench",
             "tests/unit_tests/gui/test_rocket_workbench", "tests/ui/rocket-workbench/")


def hashes():
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in sorted(set(names)) if name and (ROOT / name).is_file() and not name.startswith(PREFIX)}


def main():
    current = hashes()
    checkpoint = HERE / "source_before.json"
    if sys.argv[1:] == ["capture"]:
        assert not checkpoint.exists()
        checkpoint.write_text(json.dumps(current, indent=2) + "\n")
        print(json.dumps({"checkpointFiles": len(current)}))
        return
    original = json.loads(checkpoint.read_text())
    changed = [name for name, value in original.items() if current.get(name) != value]
    added = [name for name in current if name not in original]
    unexpected = [name for name in changed if name not in ALLOWED]
    unexpected += [name for name in added if not name.startswith(ADDITIONS)]
    result = {"pass": not unexpected, "checkpointFiles": len(original), "existingChanges": changed,
              "addedFiles": added, "unexpected": unexpected,
              "scientificSourceChanged": any(name.startswith(("core/", "physics/", "numerics/", "systems/", "api/")) for name in changed)}
    (HERE / "source_integrity.json").write_text(json.dumps(result, indent=2) + "\n")
    assert not unexpected, unexpected
    print(json.dumps({key: result[key] for key in ("pass", "checkpointFiles", "existingChanges", "unexpected", "scientificSourceChanged")}))


if __name__ == "__main__":
    main()
