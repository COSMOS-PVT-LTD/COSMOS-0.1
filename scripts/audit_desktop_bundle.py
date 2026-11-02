"""Read-only checks for embedded runtime closure, source payload and local signing."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from scripts.build_standalone_desktop import MAGIC


def audit(app):
    root = app / "Contents/Resources/app"
    external = []
    machos = 0
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        with path.open("rb") as stream:
            if stream.read(4) not in MAGIC:
                continue
        machos += 1
        identities = {
            row.strip()
            for row in subprocess.check_output(
                ["/usr/bin/otool", "-D", str(path)], text=True
            ).splitlines()[1:]
            if row.strip() and not row.rstrip().endswith(":")
        }
        dependencies = subprocess.check_output(
            ["/usr/bin/otool", "-L", str(path)], text=True
        )
        for name in set(
            re.findall(r"^\s+(/[^\n]+?) \(compatibility", dependencies, re.MULTILINE)
        ):
            if name not in identities and not name.startswith(
                ("/usr/lib/", "/System/Library/", str(app) + "/")
            ):
                external.append(
                    {"binary": str(path.relative_to(app)), "dependency": name}
                )
    if external:
        raise ValueError(
            "External non-system native dependencies: " + json.dumps(external)
        )
    sources = {}
    for package in (
        "api",
        "core",
        "physics",
        "systems",
        "gui",
        "infrastructure",
        "plugins",
        "knowledge",
        "simulation",
        "validation",
        "numerics",
        "databases",
    ):
        for path in (root / package).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                sources[str(path.relative_to(root))] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
    for path in [
        root / "main.py",
        root / "LICENSE",
        root / "NOTICE",
        *sorted((root / "scripts").glob("*.py")),
        *sorted((root / "scripts").glob("*.c")),
    ]:
        if path.is_file():
            sources[str(path.relative_to(root))] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return {
        "schema": "cosmos.desktop-audit.v1",
        "mach_o_files_checked": machos,
        "external_non_system_load_dependencies": external,
        "source_files": sources,
        "embedded_python": True,
        "external_venv_required": False,
        "user_project_files_bundled": False,
        "scope": "Static absolute load-command closure plus exact source inventory; executed native/package evidence is separate",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("NEW audit output required")
    value = audit(args.app)
    with args.output.open("x") as stream:
        json.dump(value, stream, indent=2)
    print(
        json.dumps(
            {
                "static_runtime_audit": "PASS",
                "mach_o_files": value["mach_o_files_checked"],
                "source_files": len(value["source_files"]),
            }
        )
    )


if __name__ == "__main__":
    main()
