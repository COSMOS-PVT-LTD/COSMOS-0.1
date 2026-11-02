"""P07 additions only. Existing source and earlier evidence are preserved bytewise."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREFIX = str(HERE.relative_to(ROOT)) + "/"
ADDITIONS = (PREFIX, "infrastructure/geometry/", "plugins/geometry/", "systems/geometry/",
             "tests/unit_tests/infrastructure/test_geometry_", "tests/unit_tests/plugins/test_geometry_",
             "tests/unit_tests/systems_layer/test_ngg_", "tests/integration_tests/geometry/",
             "tests/fixtures/ngg_", "tests/contracts/ngg/")


def hashes():
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(set(names))
            if name and (ROOT / name).is_file() and not name.startswith(PREFIX)}


def main():
    current = hashes()
    path = HERE / "source_before.json"
    if sys.argv[1:] == ["capture"]:
        assert not path.exists()
        path.write_text(json.dumps(current, indent=2) + "\n")
        print(json.dumps({"checkpointFiles": len(current)}))
        return
    before = json.loads(path.read_text())
    changed = [name for name, sha in before.items() if current.get(name) != sha]
    additions = sorted(name for name in current if name not in before)
    unexpected = changed + [name for name in additions if not name.startswith(ADDITIONS)]
    result = {"pass": not unexpected, "checkpointFiles": len(before), "existingChanges": changed,
              "addedFiles": additions, "unexpected": unexpected, "scientificSourceChanged": bool(changed)}
    (HERE / "source_integrity.json").write_text(json.dumps(result, indent=2) + "\n")
    assert not unexpected, unexpected
    print(json.dumps({key: result[key] for key in ("pass", "checkpointFiles", "existingChanges", "unexpected")}))


if __name__ == "__main__":
    main()
