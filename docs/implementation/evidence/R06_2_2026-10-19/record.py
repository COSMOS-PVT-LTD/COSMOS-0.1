"""Fresh R06.2 evidence; never rewrite the preceding campaign's receipts."""

from __future__ import annotations

import json
import subprocess
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sources() -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
        for directory in (
            "core", "physics", "numerics", "systems", "simulation", "validation",
            "api", "gui", "infrastructure", "plugins", "tests", "scripts",
        )
        for path in sorted((ROOT / directory).rglob("*"))
        if path.is_file() and not path.is_symlink()
        and path.suffix in {".py", ".js", ".cjs", ".ts", ".css", ".html"}
    }


def main() -> None:
    previous = json.loads((HERE.parent / "R06_2026-10-19/source-final.json").read_text())
    current = sources()
    changed = [name for name, digest in previous["sha256"].items() if current.get(name) != digest]
    assert not changed, changed
    data = {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).splitlines(),
        "previous_sources": len(previous["sha256"]),
        "previous_source_parity": True,
        "sha256": current,
    }
    with (HERE / "entry.json").open("x") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"source_count": len(current), "previous_parity": True, "head": data["head"]}))


if __name__ == "__main__":
    main()
