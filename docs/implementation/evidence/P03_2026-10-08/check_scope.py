"""Preserve all existing content except the explicitly authorized phase records."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREFIX = str(HERE.relative_to(ROOT)) + "/"
AUTHORIZED = {
    "docs/implementation/evidence/P01_2026-10-08/G1_DECISION.json",
    "docs/implementation/evidence/P01_2026-10-08/P01_REVIEW_RECORD.md",
    "docs/implementation/evidence/P01_2026-10-08/EVIDENCE_REGISTER.json",
    "docs/implementation/evidence/P02_2026-10-08/P02_DECISION.json",
}
ADDITIONS = (PREFIX, "gui/static/design-system/", "tests/js/design_system", "tests/ui/design-system/",
    "docs/implementation/evidence/P01_2026-10-08/approval/", "docs/implementation/evidence/P02_2026-10-08/completion/")


def hashes():
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    return {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in sorted(set(names))
        if n and (ROOT / n).is_file() and not n.startswith(PREFIX)}


def main():
    current = hashes()
    baseline = HERE / "source_before.json"
    if sys.argv[1:] == ["capture"]:
        assert not baseline.exists()
        baseline.write_text(json.dumps(current, indent=2) + "\n")
        print(f"Captured {len(current)} existing files")
        return
    before = json.loads(baseline.read_text())
    changes = [n for n, h in before.items() if current.get(n) != h]
    unexpected = [n for n in changes if n not in AUTHORIZED]
    additions = [n for n in current if n not in before]
    unexpected += [n for n in additions if not n.startswith(ADDITIONS)]
    result = {"pass": not unexpected, "preexistingFiles": len(before), "authorizedRecordChanges": changes,
        "unexpectedChanges": unexpected, "addedFiles": additions, "productionSourceChanged": False}
    (HERE / "source_integrity.json").write_text(json.dumps(result, indent=2) + "\n")
    assert not unexpected, unexpected
    print(json.dumps({"pass": True, "preexistingFiles": len(before), "authorizedRecords": len(changes), "unexpected": 0}))


if __name__ == "__main__":
    main()
